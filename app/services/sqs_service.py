import json

import boto3

from app.config import AWS_REGION, WORKFLOW_QUEUE_URL

#实现异步任务分发机制。工单系统作为 Producer，
# 将任务推送到消息队列，实现与下游执行 Worker 的彻底解耦
#
class SQSService:
    def __init__(self):
        self.sqs = boto3.client("sqs", region_name=AWS_REGION)
        self.queue_url = WORKFLOW_QUEUE_URL
    #打包成json消息通过http发给sqs 服务
    def send_workflow_run_message(self, workflow_run_id: str) -> None:
        if not self.queue_url:
            raise RuntimeError("WORKFLOW_QUEUE_URL is not set.")

        # 【1. 准备数据】
        # 这是一个 Python 字典（Object/Dict），存在于内存里
        message_body = {
            "workflow_run_id": workflow_run_id,
        }

        # 【2. 序列化 (Serialization)】
        # 发生在 json.dumps(message_body)
        # 它把上面的字典变成了字符串: '{"workflow_run_id": "run_xxx"}'
        
        # 【3. 发送 (Sending)】
        # 发生在 self.sqs.send_message(...)
        # 这一步通过 boto3 客户端，把序列化后的字符串通过 HTTP 请求发给 AWS SQS
        self.sqs.send_message(
            QueueUrl=self.queue_url,
            MessageBody=json.dumps(message_body), # 序列化后的结果作为参数传入
        )
    #长轮询（Long Polling）： 设置 WaitTimeSeconds=10，
    # 告诉 SQS 暂时不要立即返回空消息，而是等待最多 10 秒，看看有没有新消息进来。
    # 这样可以显著减少 Worker 的轮询次数和 HTTP 请求数，降低成本、提升实时性。
    def receive_messages(self):
        if not self.queue_url:
            raise RuntimeError("WORKFLOW_QUEUE_URL is not set.")
        response = self.sqs.receive_message(
            QueueUrl=self.queue_url,
            MaxNumberOfMessages=1,
            WaitTimeSeconds=10,  # 开启长轮询（Long Polling）
        )
        return response.get("Messages", [])
    #显式 ACK 删除机制（ReceiptHandle）： SQS 拉取消息后，消息并不会被删除，
    #而是进入隐藏的“不可见期（Visibility Timeout）”。
    #只有 Worker 在处理完任务后显式调用 delete_message，消息才算被确认消费完毕。
    def delete_message(self, receipt_handle: str) -> None:
        self.sqs.delete_message(
            QueueUrl=self.queue_url,
            ReceiptHandle=receipt_handle,
        )

