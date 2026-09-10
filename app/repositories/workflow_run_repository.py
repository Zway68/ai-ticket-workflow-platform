from typing import Optional

import boto3
from botocore.exceptions import ClientError

from app.config import AWS_REGION, WORKFLOW_RUNS_TABLE_NAME
from app.models.workflow_run_models import WorkflowRunResponse, WorkflowRunStatus

# 为后续单独查询 WorkflowRun 详情（如提供给 /workflow-runs/{id} 接口）
# 或 Worker 异步消费更新状态提供底层数据访问支撑。
class WorkflowRunRepository:
    def __init__(self):
        dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
        self.table = dynamodb.Table(WORKFLOW_RUNS_TABLE_NAME)

    def save(self, workflow_run: WorkflowRunResponse) -> WorkflowRunResponse:
        self.table.put_item(Item=self._workflow_run_to_item(workflow_run))
        return workflow_run

    def get_by_id(self, workflow_run_id: str) -> Optional[WorkflowRunResponse]:
        response = self.table.get_item(Key={"workflow_run_id": workflow_run_id})
        item = response.get("Item")

        if item is None:
            return None

        return self._item_to_workflow_run(item)
    
    # 供 Worker 消费，更新状态。
    # 这里只做单表更新
    def update_status(
        self,
        workflow_run_id: str,
        status: WorkflowRunStatus,
        updated_at: str,
        error_message: Optional[str] = None,
    ) -> Optional[WorkflowRunResponse]:
        update_expression = "SET #status = :status, updated_at = :updated_at"
        expression_attribute_names = {"#status": "status"}
        expression_attribute_values = {
            ":status": status.value,
            ":updated_at": updated_at,
        }

        if error_message is not None:
            update_expression += ", error_message = :error_message"
            expression_attribute_values[":error_message"] = error_message

        try:
            response = self.table.update_item(
                Key={"workflow_run_id": workflow_run_id},
                UpdateExpression=update_expression,
                ConditionExpression="attribute_exists(workflow_run_id)",
                ExpressionAttributeNames=expression_attribute_names,
                ExpressionAttributeValues=expression_attribute_values,
                ReturnValues="ALL_NEW",
            )

            return self._item_to_workflow_run(response["Attributes"])

        except ClientError as error:
            if error.response["Error"]["Code"] == "ConditionalCheckFailedException":
                return None
            raise
    #工具方法：将对象转为 DynamoDB Item
    def _workflow_run_to_item(self, workflow_run: WorkflowRunResponse) -> dict:
        item = {
            "workflow_run_id": workflow_run.workflow_run_id,
            "ticket_id": workflow_run.ticket_id,
            "workflow_id": workflow_run.workflow_id,
            "workflow_type": workflow_run.workflow_type,
            "status": workflow_run.status.value,
            "workflow_input": workflow_run.workflow_input,
            "created_at": workflow_run.created_at,
            "updated_at": workflow_run.updated_at,
            "result": workflow_run.result
        }

        if workflow_run.error_message is not None:
            item["error_message"] = workflow_run.error_message

        return item
    #工具方法：将 DynamoDB Item 转为对象
    def _item_to_workflow_run(self, item: dict) -> WorkflowRunResponse:
        return WorkflowRunResponse(
            workflow_run_id=item["workflow_run_id"],
            ticket_id=item["ticket_id"],
            workflow_id=item["workflow_id"],
            workflow_type=item["workflow_type"],
            status=WorkflowRunStatus(item["status"]),
            workflow_input=item.get("workflow_input", {}),
            created_at=item["created_at"],
            updated_at=item["updated_at"],
            error_message=item.get("error_message"),
            result=item.get("result", {})
        )
