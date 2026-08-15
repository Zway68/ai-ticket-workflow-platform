from typing import List, Optional

import boto3
from botocore.exceptions import ClientError

from app.models.ticket_models import TicketResponse, TicketStatus


class TicketRepository:
    def __init__(self):
        # 建立 DynamoDB 资源连接
        dynamodb = boto3.resource("dynamodb", region_name="us-west-2")
        self.table = dynamodb.Table("Tickets")

    def save(self, ticket: TicketResponse) -> TicketResponse:
        # 将工单写入 DynamoDB 表
        self.table.put_item(
            Item={
                "ticket_id": ticket.ticket_id,
                "user_id": ticket.user_id,
                "message": ticket.message,
                "source": ticket.source,
                "status": ticket.status.value,
                "created_at": ticket.created_at,
                "updated_at": ticket.updated_at,
            }
        )
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
        )


ticket_repository = TicketRepository()
