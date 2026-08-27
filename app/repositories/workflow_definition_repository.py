from decimal import Decimal
from typing import List, Optional
import boto3
from boto3.dynamodb.conditions import Attr
from app.config import AWS_REGION, WORKFLOW_DEFINITIONS_TABLE_NAME
from app.models.workflow_definition_models import (
    WorkflowDefinitionResponse,
    WorkflowDefinitionStatus,
)

class WorkflowDefinitionRepository:
    """工作流定义仓库层 (Repository Layer)

    负责直接与 AWS DynamoDB 交互，处理 WorkflowDefinitions 表的 CRUD 操作。
    """

    def __init__(self, table=None):
        if table is not None:
            self.table = table
        else:
            # 建立 DynamoDB 资源连接并绑定目标表
            dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
            self.table = dynamodb.Table(WORKFLOW_DEFINITIONS_TABLE_NAME)

    def save(
        self,
        workflow_definition: WorkflowDefinitionResponse,
    ) -> WorkflowDefinitionResponse:
        """保存或更新工作流定义记录

        1. 将 Pydantic 模型导出为纯 JSON 可接受的字典结构 (model_dump(mode="json"))。
        2. 将 float 类型的 min_confidence_score 转为 Decimal，防止 boto3/DynamoDB 类型报错。
        3. 调用 table.put_item() 写入/覆盖 DynamoDB 中的记录。
        """
        # Pydantic 模型转换为字典 (Dictionary)
        item = workflow_definition.model_dump(mode="json")

        # AWS DynamoDB 的 Python SDK (boto3) 不支持标准的 Python float 类型，需转为 Decimal
        item["min_confidence_score"] = Decimal(
            str(item["min_confidence_score"])
        )

        # 写入 DynamoDB 数据表
        self.table.put_item(Item=item)

        return workflow_definition

    def get_by_id(
        self,
        workflow_id: str,
    ) -> Optional[WorkflowDefinitionResponse]:
        """根据唯一标识 workflow_id 查询单条工作流定义

        若记录不存在，返回 None；若找到记录，通过解包将字典还原为 WorkflowDefinitionResponse 模型。
        """
        response = self.table.get_item(
            Key={
                "workflow_id": workflow_id
            }
        )

        # 从 API 响应中提取记录字典 Item
        item = response.get("Item")

        if item is None:
            return None

        # 将字典解包 (**item) 并还原为 Pydantic 数据模型对象
        return WorkflowDefinitionResponse(**item)

    def list_all(self) -> List[WorkflowDefinitionResponse]:
        """全表扫描 (Scan) 获取系统中所有的工作流定义记录"""
        response = self.table.scan()
        # "Items" 对应的是一个包含多条记录字典的列表 [dict, dict, ...]
        items = response.get("Items", [])

        # 列表推导式：将列表中的每个字典转换为 WorkflowDefinitionResponse 对象
        return [
            WorkflowDefinitionResponse(**item)
            for item in items
        ]

    def list_published(self) -> List[WorkflowDefinitionResponse]:
        """全表扫描并使用 FilterExpression 仅获取状态为已发布 (PUBLISHED) 的工作流定义列表"""
        response = self.table.scan(
            # 过滤条件：只选择 status 属性为 PUBLISHED 的记录
            FilterExpression=Attr("status").eq(
                WorkflowDefinitionStatus.PUBLISHED.value
            )
        )

        items = response.get("Items", [])

        return [
            WorkflowDefinitionResponse(**item)
            for item in items
        ]


# 导出仓库层单例实例
workflow_definition_repository = WorkflowDefinitionRepository()

