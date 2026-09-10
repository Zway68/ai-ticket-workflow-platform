import json
from datetime import datetime, timezone

from app.repositories.workflow_run_repository import WorkflowRunRepository
from app.repositories.workflow_transaction_repository import WorkflowTransactionRepository
from app.services.sqs_service import SQSService
from app.workflows.workflow_handlers import run_workflow_handler

#收消息（SQS） ➔ 查数据（RunRepo） ➔ 原子抢占并更新（TransactRepo）
# ➔ 业务处理(Handler) ➔ 更新状态（TransactRepo+RunRepo） ➔ 删除消息（SQS）
class WorkflowWorker:
    def __init__(self):
        self.sqs_service = SQSService()
        self.workflow_run_repository = WorkflowRunRepository() #Worker 需要WorkflowRunResponse对象 找到对应的Handler
        self.workflow_transaction_repository = WorkflowTransactionRepository()

    def run(self):
        print("Workflow worker started...")

        while True:
            messages = self.sqs_service.receive_messages()

            if not messages:
                print("No messages received.")
                continue

            for message in messages:
                self.process_message(message)

    def process_message(self, message: dict):
        receipt_handle = message["ReceiptHandle"]
        body = json.loads(message["Body"])
        workflow_run_id = body["workflow_run_id"]

        print(f"Received workflow_run_id: {workflow_run_id}")

        workflow_run = self.workflow_run_repository.get_by_id(workflow_run_id)
        # 场景 ①：数据不存在 / 脏消息
        if workflow_run is None:
            print(f"Workflow run not found: {workflow_run_id}")
            self.sqs_service.delete_message(receipt_handle)# 👈 删！避免无效消息一直死循环拉取
            return


        claimed = self.workflow_transaction_repository.mark_workflow_running_if_queued(
            ticket_id=workflow_run.ticket_id,
            workflow_run_id=workflow_run.workflow_run_id,
            updated_at=self._current_time_iso(),
        )
        # 场景 ②：重复消息 / 抢占失败 幂等防护
        if not claimed:
            print(
                "Workflow run was already claimed or processed. "
                f"Skipping duplicate message: {workflow_run_id}"
            )
            self.sqs_service.delete_message(receipt_handle)# 👈 删！说明别的 Worker 已经在跑或跑完了，本条重复消息功成身退
            return

        # 场景 ③：任务成功执行完成
        try:
            #执行业务 Handler
            result = run_workflow_handler(workflow_run)
            #标记完成
            self.workflow_transaction_repository.mark_workflow_completed(
                ticket_id=workflow_run.ticket_id,
                workflow_run_id=workflow_run.workflow_run_id,
                result=result,
                updated_at=self._current_time_iso(),
            )
            # 成功删除消息，避免 SQS 重试
            self.sqs_service.delete_message(receipt_handle)# 👈 删！正常完成，告诉 SQS 任务已圆满结束
            print(f"Workflow run completed: {workflow_run_id}")

        # 场景 ④：任务执行报错（但已在数据库标记为 FAILED）
        except Exception as error:
            self.workflow_transaction_repository.mark_workflow_failed(
                ticket_id=workflow_run.ticket_id,
                workflow_run_id=workflow_run.workflow_run_id,
                error_message=str(error),
                updated_at=self._current_time_iso(),
            )

            self.sqs_service.delete_message(receipt_handle) # 👈 删！错误信息已持久化记录，防止 SQS 无限重试毒消息
            print(f"Workflow run failed: {workflow_run_id}. Error: {error}")

    def _current_time_iso(self):
        return datetime.now(timezone.utc).isoformat()


if __name__ == "__main__":
    worker = WorkflowWorker()
    worker.run()
