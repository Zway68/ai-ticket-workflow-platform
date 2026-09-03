"""
LLM 工作流选择器服务模块。

本模块通过调用 OpenAI 大语言模型，根据用户输入的自然语言消息，
自动匹配最合适的工作流定义，并提取相关字段信息。

核心流程：
    1. 获取所有已发布的工作流定义
    2. 将用户消息和工作流定义发送给 OpenAI 模型
    3. 模型返回结构化的 JSON 选择结果
    4. 解析并构建标准化的响应对象
"""

import json
from typing import Any, Dict, List, Optional

from openai import OpenAI

from app.config import OPENAI_MODEL
from app.models.workflow_definition_models import WorkflowDefinitionResponse
from app.models.workflow_selector_models import (
    WorkflowSelectionRequest,
    WorkflowSelectionResponse,
)
from app.services.workflow_definition_service import workflow_definition_service


class LLMWorkflowSelectorService:
    """
    基于 LLM 的工作流选择器服务。

    该服务利用 OpenAI 大语言模型，将用户的自然语言描述
    智能匹配到最合适的预定义工作流，同时自动提取用户消息中
    包含的字段信息，并识别缺失的必填字段。

    Attributes:
        client: OpenAI API 客户端实例。
        workflow_service: 工作流定义服务，用于获取已发布的工作流列表。
    """

    def __init__(
        self,
        client: Any = None,
        workflow_service: Any = None,
    ):
        """
        初始化 LLM 工作流选择器服务。

        Args:
            client: OpenAI 客户端实例，为 None 时自动创建默认客户端。
                    支持依赖注入，便于单元测试时传入 mock 对象。
            workflow_service: 工作流定义服务实例，为 None 时使用默认的单例服务。
                              支持依赖注入，便于单元测试时传入 mock 对象。
        """
        self.client = client or OpenAI()
        self.workflow_service = workflow_service or workflow_definition_service

    def select_workflow(
        self,
        request: WorkflowSelectionRequest,
    ) -> WorkflowSelectionResponse:
        """
        根据用户请求选择最匹配的工作流。

        这是对外暴露的主方法，协调整个选择流程：
        获取工作流定义 → 调用 LLM 分析 → 构建标准化响应。

        Args:
            request: 工作流选择请求，包含用户输入的自然语言消息。

        Returns:
            WorkflowSelectionResponse: 包含选中的工作流信息、置信度、
            提取的字段、缺失字段等完整的选择结果。
        """
        # 获取所有已发布的工作流定义
        workflow_definitions = (
            self.workflow_service.list_published_workflow_definitions()
        )

        # 如果没有可用的工作流定义，直接返回空结果
        if not workflow_definitions:
            return WorkflowSelectionResponse(
                selected_workflow_id=None,
                selected_workflow_type=None,
                confidence_score=0.0,
                reason="No published workflow definitions are available.",
                extracted_fields={},
                missing_fields=[],
                missing_field_questions=[],
                is_ready_for_workflow=False,
            )

        # 调用 OpenAI 模型进行工作流选择
        raw_selection = self._call_openai(
            user_message=request.message,
            workflow_definitions=workflow_definitions,
        )

        # 将 LLM 的原始返回结果构建为标准化响应
        return self._build_response(
            raw_selection=raw_selection,
            workflow_definitions=workflow_definitions,
        )

    def _call_openai(
        self,
        user_message: str,
        workflow_definitions: List[WorkflowDefinitionResponse],
    ) -> Dict:
        """
        调用 OpenAI API 执行工作流选择推理。

        构造系统提示词和用户提示词，使用 JSON Schema 约束模型的输出格式，
        确保返回结构化的选择结果。

        Args:
            user_message: 用户输入的自然语言消息。
            workflow_definitions: 所有已发布的工作流定义列表。

        Returns:
            Dict: LLM 返回的原始 JSON 选择结果，包含以下字段：
                - selected_workflow_id: 选中的工作流 ID（可能为 null）
                - selected_workflow_type: 选中的工作流类型（可能为 null）
                - confidence_score: 置信度评分 (0~1)
                - reason: 选择理由说明
                - extracted_fields: 从用户消息中提取的字段列表
                - missing_fields: 缺失的必填字段名称列表
                - missing_field_questions: 针对缺失字段的追问问题列表
        """
        # 系统提示词：定义 LLM 的角色和行为规则
        system_prompt = """
You are a workflow selection engine for a client issue triage platform.

Your job:
1. Read the user's message.
2. Review all available workflow definitions.
3. Select the best matching workflow.
4. Extract required and optional fields from the user message.
5. Identify missing required fields.
6. Return a confidence score between 0 and 1.

Rules:
- Only select a workflow from the provided workflow definitions.
- If none of the workflows match, selected_workflow_id must be null.
- Do not invent extracted field values.
- If a required field is missing, include it in missing_fields.
- Use the workflow definition's missing_field_question when possible.
- confidence_score is your estimated confidence in the selected workflow.
"""

        # 将工作流定义格式化为 LLM 可读的文本
        workflow_definitions_text = self._format_workflow_definitions(
            workflow_definitions
        )

        # 用户提示词：包含用户消息和可用的工作流定义
        user_prompt = f"""
User message:
{user_message}

Available workflow definitions:
{workflow_definitions_text}

Return the workflow selection result as JSON.
"""

        # 调用 OpenAI Responses API，使用 JSON Schema 强制结构化输出
        response = self.client.responses.create(
            model=OPENAI_MODEL,
            input=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
            text={
                "format": {
                    "type": "json_schema",
                    "name": "workflow_selection_result",
                    "strict": True,  # 严格模式：确保输出完全符合 schema
                    "schema": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "selected_workflow_id": {
                                "type": ["string", "null"]
                            },
                            "selected_workflow_type": {
                                "type": ["string", "null"]
                            },
                            "confidence_score": {
                                "type": "number"
                            },
                            "reason": {
                                "type": "string"
                            },
                            "extracted_fields": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "additionalProperties": False,
                                    "properties": {
                                        "field_name": {
                                            "type": "string"
                                        },
                                        "field_value": {
                                            "type": "string"
                                        },
                                    },
                                    "required": [
                                        "field_name",
                                        "field_value",
                                    ],
                                },
                            },
                            "missing_fields": {
                                "type": "array",
                                "items": {
                                    "type": "string"
                                },
                            },
                            "missing_field_questions": {
                                "type": "array",
                                "items": {
                                    "type": "string"
                                },
                            },
                        },
                        "required": [
                            "selected_workflow_id",
                            "selected_workflow_type",
                            "confidence_score",
                            "reason",
                            "extracted_fields",
                            "missing_fields",
                            "missing_field_questions",
                        ],
                    },
                }
            },
        )

        # 解析 LLM 返回的 JSON 文本为 Python 字典
        return json.loads(response.output_text)

    def _format_workflow_definitions(
        self,
        workflow_definitions: List[WorkflowDefinitionResponse],
    ) -> str:
        """
        将工作流定义列表格式化为 JSON 字符串，供 LLM 提示词使用。

        仅保留 LLM 决策所需的关键字段，过滤掉不必要的内部字段，
        以减少 token 消耗并提高模型的理解准确度。

        Args:
            workflow_definitions: 工作流定义响应对象列表。

        Returns:
            str: 格式化后的 JSON 字符串（带缩进，便于 LLM 阅读）。
        """
        simplified_definitions = []

        for workflow in workflow_definitions:
            # 提取每个工作流的核心字段，构建精简版定义
            simplified_definitions.append(
                {
                    "workflow_id": workflow.workflow_id,
                    "workflow_type": workflow.workflow_type,
                    "name": workflow.name,
                    "description": workflow.description,
                    "trigger_examples": workflow.trigger_examples,  # 触发示例，帮助 LLM 理解匹配模式
                    "required_fields": [
                        field.model_dump(mode="json")
                        for field in workflow.required_fields
                    ],
                    "optional_fields": [
                        field.model_dump(mode="json")
                        for field in workflow.optional_fields
                    ],
                    "min_confidence_score": workflow.min_confidence_score,  # 最低置信度阈值
                }
            )

        return json.dumps(simplified_definitions, indent=2)

    def _build_response(
        self,
        raw_selection: Dict,
        workflow_definitions: List[WorkflowDefinitionResponse],
    ) -> WorkflowSelectionResponse:
        """
        将 LLM 的原始选择结果构建为标准化的响应对象。

        该方法负责：
        1. 查找选中的工作流定义（用于校验置信度阈值）
        2. 标准化提取的字段格式（数组 → 字典）
        3. 判断是否满足工作流执行条件（is_ready_for_workflow）

        Args:
            raw_selection: LLM 返回的原始 JSON 字典。
            workflow_definitions: 所有已发布的工作流定义列表。

        Returns:
            WorkflowSelectionResponse: 标准化的工作流选择响应对象。
        """
        selected_workflow_id = raw_selection.get("selected_workflow_id")

        # 根据 LLM 选择的 workflow_id 查找对应的工作流定义
        selected_workflow = self._find_workflow_definition(
            selected_workflow_id=selected_workflow_id,
            workflow_definitions=workflow_definitions,
        )

        confidence_score = float(raw_selection.get("confidence_score", 0.0))
        missing_fields = raw_selection.get("missing_fields", [])

        # 将 LLM 返回的数组格式 [{field_name, field_value}] 转换为字典格式 {name: value}
        extracted_fields = self._normalize_extracted_fields(
            raw_selection.get("extracted_fields", [])
        )

        # 判断是否可以直接执行工作流：
        # 条件1：置信度 >= 工作流定义的最低阈值
        # 条件2：没有缺失的必填字段
        is_ready_for_workflow = False

        if selected_workflow is not None:
            is_ready_for_workflow = (
                confidence_score >= selected_workflow.min_confidence_score
                and len(missing_fields) == 0
            )

        return WorkflowSelectionResponse(
            selected_workflow_id=raw_selection.get("selected_workflow_id"),
            selected_workflow_type=raw_selection.get("selected_workflow_type"),
            confidence_score=confidence_score,
            reason=raw_selection.get("reason", ""),
            extracted_fields=extracted_fields,
            missing_fields=missing_fields,
            missing_field_questions=raw_selection.get(
                "missing_field_questions",
                [],
            ),
            is_ready_for_workflow=is_ready_for_workflow,
        )

    def _normalize_extracted_fields(self, raw_fields: List[Dict]) -> Dict[str, str]:
        """
        将提取的字段从数组格式标准化为字典格式。

        LLM 返回的 extracted_fields 是数组格式：
            [{"field_name": "name", "field_value": "value"}, ...]
        本方法将其转换为更易使用的字典格式：
            {"name": "value", ...}

        Args:
            raw_fields: LLM 返回的原始字段数组。

        Returns:
            Dict[str, str]: 字段名到字段值的映射字典。
                            跳过 field_name 或 field_value 为空的条目。
        """
        extracted_fields = {}

        for field in raw_fields:
            field_name = field.get("field_name")
            field_value = field.get("field_value")

            # 仅保留名称和值都非空的字段
            if field_name and field_value:
                extracted_fields[field_name] = field_value

        return extracted_fields

    def _find_workflow_definition(
        self,
        selected_workflow_id: Optional[str],
        workflow_definitions: List[WorkflowDefinitionResponse],
    ) -> Optional[WorkflowDefinitionResponse]:
        """
        根据工作流 ID 在定义列表中查找对应的工作流。

        Args:
            selected_workflow_id: LLM 选择的工作流 ID，可能为 None。
            workflow_definitions: 所有已发布的工作流定义列表。

        Returns:
            Optional[WorkflowDefinitionResponse]: 匹配的工作流定义对象，
            未找到时返回 None。
        """
        if selected_workflow_id is None:
            return None

        for workflow in workflow_definitions:
            if workflow.workflow_id == selected_workflow_id:
                return workflow

        return None


# 导出的单例服务
llm_workflow_selector_service = LLMWorkflowSelectorService()
