import boto3
from boto3.dynamodb.types import TypeSerializer

from app.config import AWS_REGION, TICKETS_TABLE_NAME, WORKFLOW_RUNS_TABLE_NAME
from app.models.ticket_models import TicketStatus
from app.models.workflow_run_models import WorkflowRunResponse, WorkflowRunStatus
from botocore.exceptions import ClientError

#保证双表状态的一致性（Atomic All-or-Nothing）。
# 避免出现“WorkflowRun 写入成功但 Ticket 未能绑定”
# 或者“Ticket 显示已排队但 WorkflowRun 状态仍为新建”的数据不一致裂脑问题。
class WorkflowTransactionRepository:
    def __init__(self):
        self.client = boto3.client("dynamodb", region_name=AWS_REGION)
        self.serializer = TypeSerializer()

#在一个原子事务内，向 WorkflowRuns 表 Put 新运行实例，
# 同时 Update Tickets 表将其状态置为 WORKFLOW_CREATED 
# 并关联 workflow_run_id
    def create_workflow_run_and_attach_ticket(
        self,
        workflow_run: WorkflowRunResponse,
        extracted_fields: dict,
        updated_at: str,
    ) -> None:
        workflow_run_item = {
            "workflow_run_id": workflow_run.workflow_run_id,
            "ticket_id": workflow_run.ticket_id,
            "workflow_id": workflow_run.workflow_id,
            "workflow_type": workflow_run.workflow_type,
            "status": workflow_run.status.value,
            "workflow_input": workflow_run.workflow_input,
            "created_at": workflow_run.created_at,
            "updated_at": workflow_run.updated_at,
        }

        self.client.transact_write_items(
            TransactItems=[
                {
                    "Put": {
                        "TableName": WORKFLOW_RUNS_TABLE_NAME,
                        "Item": self._serialize_item(workflow_run_item),
                        "ConditionExpression": "attribute_not_exists(workflow_run_id)",
                    }
                },
                {
                    "Update": {
                        "TableName": TICKETS_TABLE_NAME,
                        "Key": self._serialize_item({"ticket_id": workflow_run.ticket_id}),
                        "UpdateExpression": (
                            "SET #status = :status, "
                            "selected_workflow_id = :workflow_id, "
                            "selected_workflow_type = :workflow_type, "
                            "workflow_run_id = :workflow_run_id, "
                            "extracted_fields = :extracted_fields, "
                            "missing_fields = :missing_fields, "
                            "missing_field_questions = :missing_field_questions, "
                            "updated_at = :updated_at"
                        ),
                        "ConditionExpression": "attribute_exists(ticket_id)",
                        "ExpressionAttributeNames": {"#status": "status"},
                        "ExpressionAttributeValues": self._serialize_item(
                            {
                                ":status": TicketStatus.WORKFLOW_CREATED.value,
                                ":workflow_id": workflow_run.workflow_id,
                                ":workflow_type": workflow_run.workflow_type,
                                ":workflow_run_id": workflow_run.workflow_run_id,
                                ":extracted_fields": extracted_fields,
                                ":missing_fields": [],
                                ":missing_field_questions": [],
                                ":updated_at": updated_at,
                            }
                        ),
                    }
                },
            ]
        )
    #原子抢占任务
    #同一个任务可能被两个 Worker 同时拉到。
    #通过 ConditionExpression = "#status = :queued" 确保只有一个 Worker 能成功修改状态。
    # 返回 True 表示成功抢占，可以开始执行；False 表示已被抢占（竞态失败）。
    def mark_workflow_running_if_queued(
        self,
        ticket_id: str,
        workflow_run_id: str,
        updated_at: str,
    ) -> bool:
        try:
            self.client.transact_write_items(
                TransactItems=[
                    {
                        "Update": {
                            "TableName": WORKFLOW_RUNS_TABLE_NAME,
                            "Key": self._serialize_item({"workflow_run_id": workflow_run_id}),
                            "UpdateExpression": "SET #status = :running, updated_at = :updated_at",
                            # 核心条件检查：只有当前状态是 QUEUED 才允许更新
                            "ConditionExpression": "#status = :queued",
                            "ExpressionAttributeNames": {"#status": "status"},
                            "ExpressionAttributeValues": self._serialize_item(
                                {
                                    ":running": WorkflowRunStatus.RUNNING.value,
                                    ":queued": WorkflowRunStatus.QUEUED.value,
                                    ":updated_at": updated_at,
                                }
                            ),
                        }
                    },
                    {
                        "Update": {
                            "TableName": TICKETS_TABLE_NAME,
                            "Key": self._serialize_item({"ticket_id": ticket_id}),
                            "UpdateExpression": "SET #status = :status, updated_at = :updated_at",
                            # 确保该 Ticket 确实存在
                            "ConditionExpression": "attribute_exists(ticket_id)",
                            "ExpressionAttributeNames": {"#status": "status"},
                            "ExpressionAttributeValues": self._serialize_item(
                                {
                                    ":status": TicketStatus.WORKFLOW_RUNNING.value,
                                    ":updated_at": updated_at,
                                }
                            ),
                        }
                    },
                ]
            )
            return True
        except ClientError as error:
            #如果条件不满足（已被抢占），DynamoDB 会抛出 TransactionCanceledException
            if error.response["Error"]["Code"] == "TransactionCanceledException":
                return False
            raise
    
    #工作流成功结束双表联动
    #使用 ConditionExpression 确保只有 RUNNING 的 Workflow 才允许结束(防止重复操作)
    def mark_workflow_completed(
        self,
        ticket_id: str,
        workflow_run_id: str,
        result: dict,
        updated_at: str,
    ) -> None:
        self.client.transact_write_items(
            TransactItems=[
                {
                    "Update": {
                        "TableName": WORKFLOW_RUNS_TABLE_NAME,
                        "Key": self._serialize_item({"workflow_run_id": workflow_run_id}),
                        "UpdateExpression": (
                            "SET #status = :status, #result = :result, updated_at = :updated_at"
                        ),
                        "ConditionExpression": "attribute_exists(workflow_run_id)",
                        "ExpressionAttributeNames": {"#status": "status", "#result": "result"},
                        "ExpressionAttributeValues": self._serialize_item(
                            {
                                ":status": WorkflowRunStatus.COMPLETED.value,
                                ":result": result,
                                ":updated_at": updated_at,
                            }
                        ),
                    }
                },
                {
                    "Update": {
                        "TableName": TICKETS_TABLE_NAME,
                        "Key": self._serialize_item({"ticket_id": ticket_id}),
                        "UpdateExpression": "SET #status = :status, updated_at = :updated_at",
                        "ConditionExpression": "attribute_exists(ticket_id)",
                        "ExpressionAttributeNames": {"#status": "status"},
                        "ExpressionAttributeValues": self._serialize_item(
                            {
                                ":status": TicketStatus.RESOLVED.value,
                                ":updated_at": updated_at,
                            }
                        ),
                    }
                },
            ]
        )
    
#在一个原子事务内，同时将 WorkflowRuns.status 更新为 QUEUED，
#并将 Ticket.status 更新为 WORKFLOW_QUEUED
    def mark_workflow_queued(
        self,
        ticket_id: str,
        workflow_run_id: str,
        updated_at: str,
    ) -> None:
        self.client.transact_write_items(
            TransactItems=[
                {
                    "Update": {
                        "TableName": WORKFLOW_RUNS_TABLE_NAME,
                        "Key": self._serialize_item({"workflow_run_id": workflow_run_id}),
                        "UpdateExpression": "SET #status = :status, updated_at = :updated_at",
                        "ConditionExpression": "attribute_exists(workflow_run_id)",
                        "ExpressionAttributeNames": {"#status": "status"},
                        "ExpressionAttributeValues": self._serialize_item(
                            {
                                ":status": WorkflowRunStatus.QUEUED.value,
                                ":updated_at": updated_at,
                            }
                        ),
                    }
                },
                {
                    "Update": {
                        "TableName": TICKETS_TABLE_NAME,
                        "Key": self._serialize_item({"ticket_id": ticket_id}),
                        "UpdateExpression": "SET #status = :status, updated_at = :updated_at",
                        "ConditionExpression": "attribute_exists(ticket_id)",
                        "ExpressionAttributeNames": {"#status": "status"},
                        "ExpressionAttributeValues": self._serialize_item(
                            {
                                ":status": TicketStatus.WORKFLOW_QUEUED.value,
                                ":updated_at": updated_at,
                            }
                        ),
                    }
                },
            ]
        )
# 在 SQS 发送失败时，在一个原子事务内，将WorkflowRuns.status
# 和Ticket.status两者都标记为 FAILED 并记录错误信息
    def mark_workflow_failed(
        self,
        ticket_id: str,
        workflow_run_id: str,
        error_message: str,
        updated_at: str,
    ) -> None:
        self.client.transact_write_items(
            TransactItems=[
                {
                    "Update": {
                        "TableName": WORKFLOW_RUNS_TABLE_NAME,
                        "Key": self._serialize_item({"workflow_run_id": workflow_run_id}),
                        "UpdateExpression": (
                            "SET #status = :status, "
                            "error_message = :error_message, "
                            "updated_at = :updated_at"
                        ),
                        "ConditionExpression": "attribute_exists(workflow_run_id)",
                        "ExpressionAttributeNames": {"#status": "status"},
                        "ExpressionAttributeValues": self._serialize_item(
                            {
                                ":status": WorkflowRunStatus.FAILED.value,
                                ":error_message": error_message,
                                ":updated_at": updated_at,
                            }
                        ),
                    }
                },
                {
                    "Update": {
                        "TableName": TICKETS_TABLE_NAME,
                        "Key": self._serialize_item({"ticket_id": ticket_id}),
                        "UpdateExpression": "SET #status = :status, updated_at = :updated_at",
                        "ConditionExpression": "attribute_exists(ticket_id)",
                        "ExpressionAttributeNames": {"#status": "status"},
                        "ExpressionAttributeValues": self._serialize_item(
                            {
                                ":status": TicketStatus.FAILED.value,
                                ":updated_at": updated_at,
                            }
                        ),
                    }
                },
            ]
        )
# 辅助方法，将字典序列化为 DynamoDB 格式
    def _serialize_item(self, item: dict) -> dict:
        return {key: self.serializer.serialize(value) for key, value in item.items()}


