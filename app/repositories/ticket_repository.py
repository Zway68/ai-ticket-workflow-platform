from typing import List, Optional

import boto3
from botocore.exceptions import ClientError

from app.config import AWS_REGION, TICKETS_TABLE_NAME
from app.models.ticket_models import TicketResponse, TicketStatus


class TicketRepository:
    def __init__(self, table=None):
        dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
        self.table = dynamodb.Table(TICKETS_TABLE_NAME)

    def save(self, ticket: TicketResponse) -> TicketResponse:
        # 将工单写入 DynamoDB 表
        self.table.put_item(Item=self._ticket_to_item(ticket))
        return ticket

    def get_by_id(self, ticket_id: str) -> Optional[TicketResponse]:
        # 根据 ticket_id 查询单条记录
        response = self.table.get_item(
            Key={
                "ticket_id": ticket_id
            }
        )
        item = response.get("Item")
        if item is None:
            return None
        return self._item_to_ticket(item)

    def list_all(self) -> List[TicketResponse]:
        # 全表扫描获取所有工单列表
        response = self.table.scan()
        items = response.get("Items", [])
        return [
            self._item_to_ticket(item)
            for item in items
        ]

    def update_status(
        self,
        ticket_id: str,
        status: TicketStatus,
        updated_at: str,
    ) -> Optional[TicketResponse]:
        # 使用 UpdateExpression 原子更新工单状态及更新时间
        try:
            response = self.table.update_item(
                Key={
                    "ticket_id": ticket_id
                },
                UpdateExpression="SET #status = :status, updated_at = :updated_at",
                ExpressionAttributeNames={
                    "#status": "status"
                },
                ExpressionAttributeValues={
                    ":status": status.value,
                    ":updated_at": updated_at,
                },
                ReturnValues="ALL_NEW",
            )
            updated_item = response.get("Attributes")
            if updated_item is None:
                return None
            return self._item_to_ticket(updated_item)
        except ClientError:
            return None
    
    def mark_waiting_for_input(
        self,
        ticket_id: str,
        selected_workflow_id: Optional[str],
        selected_workflow_type: Optional[str],
        extracted_fields: dict,
        missing_fields: list,
        missing_field_questions: list,
        updated_at: str,
    ) -> Optional[TicketResponse]:
        # 通过 DynamoDB update_item 
        # 写入 AI 提取结果及追问列表，并将状态更新为 WAITING_FOR_INPUT。
        try:
            response = self.table.update_item(
                Key={"ticket_id": ticket_id},
                UpdateExpression=(
                    "SET #status = :status, "
                    "selected_workflow_id = :selected_workflow_id, "
                    "selected_workflow_type = :selected_workflow_type, "
                    "extracted_fields = :extracted_fields, "
                    "missing_fields = :missing_fields, "
                    "missing_field_questions = :missing_field_questions, "
                    "updated_at = :updated_at"
                ),
                ConditionExpression="attribute_exists(ticket_id)",
                ExpressionAttributeNames={"#status": "status"},
                ExpressionAttributeValues={
                    ":status": TicketStatus.WAITING_FOR_INPUT.value,
                    ":selected_workflow_id": selected_workflow_id,
                    ":selected_workflow_type": selected_workflow_type,
                    ":extracted_fields": extracted_fields,
                    ":missing_fields": missing_fields,
                    ":missing_field_questions": missing_field_questions,
                    ":updated_at": updated_at,
                },
                ReturnValues="ALL_NEW",
            )

            return self._item_to_ticket(response["Attributes"])

        except ClientError as error:
            if error.response["Error"]["Code"] == "ConditionalCheckFailedException":
                return None
            raise

    def _ticket_to_item(self, ticket: TicketResponse) -> dict:
        # 辅助方法：将 Pydantic TicketResponse 模型序列化为 DynamoDB 字典
        return {
            "ticket_id": ticket.ticket_id,
            "user_id": ticket.user_id,
            "message": ticket.message,
            "source": ticket.source,
            "status": ticket.status.value,
            "created_at": ticket.created_at,
            "updated_at": ticket.updated_at,
            "selected_workflow_id": ticket.selected_workflow_id,
            "selected_workflow_type": ticket.selected_workflow_type,
            "workflow_run_id": ticket.workflow_run_id,
            "extracted_fields": ticket.extracted_fields,
            "missing_fields": ticket.missing_fields,
            "missing_field_questions": ticket.missing_field_questions,
        }
    def _item_to_ticket(self, item: dict) -> TicketResponse:
        # 辅助方法：将 DynamoDB 的字典数据反序列化回 Pydantic TicketResponse 模型
        return TicketResponse(
            ticket_id=item["ticket_id"],
            user_id=item["user_id"],
            message=item["message"],
            source=item.get("source", "unknown"),
            status=TicketStatus(item["status"]),
            created_at=item["created_at"],
            updated_at=item["updated_at"],
            selected_workflow_id=item.get("selected_workflow_id"),
            selected_workflow_type=item.get("selected_workflow_type"),
            workflow_run_id=item.get("workflow_run_id"),
            extracted_fields=item.get("extracted_fields", {}),
            missing_fields=item.get("missing_fields", []),
            missing_field_questions=item.get("missing_field_questions", []),
        )


ticket_repository = TicketRepository()
