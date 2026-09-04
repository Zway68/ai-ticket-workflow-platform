import os


AWS_REGION = os.getenv("AWS_REGION", "us-west-2")

WORKFLOW_DEFINITIONS_TABLE_NAME = os.getenv(
    "WORKFLOW_DEFINITIONS_TABLE_NAME",
    "WorkflowDefinitions",
)

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5")

TICKETS_TABLE_NAME = os.getenv("TICKETS_TABLE_NAME", "Tickets")
WORKFLOW_RUNS_TABLE_NAME = os.getenv("WORKFLOW_RUNS_TABLE_NAME", "WorkflowRuns")
WORKFLOW_QUEUE_URL = os.getenv("WORKFLOW_QUEUE_URL", "https://sqs.us-west-2.amazonaws.com/150460248886/ticket-workflow-queue")
