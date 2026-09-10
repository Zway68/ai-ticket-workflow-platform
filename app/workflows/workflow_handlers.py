import time

from app.models.workflow_run_models import WorkflowRunResponse


def handle_stock_data_issue(workflow_run: WorkflowRunResponse) -> dict:
    print("Running stock data issue workflow...")
    print(f"Workflow input: {workflow_run.workflow_input}")
    time.sleep(2)
    return {
        "message": "Stock data issue workflow completed.",
        "workflow_type": workflow_run.workflow_type,
    }


def handle_watchlist_bug(workflow_run: WorkflowRunResponse) -> dict:
    print("Running watchlist bug workflow...")
    print(f"Workflow input: {workflow_run.workflow_input}")
    time.sleep(2)
    return {
        "message": "Watchlist bug workflow completed.",
        "workflow_type": workflow_run.workflow_type,
    }


def handle_price_alert_bug(workflow_run: WorkflowRunResponse) -> dict:
    print("Running price alert bug workflow...")
    print(f"Workflow input: {workflow_run.workflow_input}")
    time.sleep(2)
    return {
        "message": "Price alert bug workflow completed.",
        "workflow_type": workflow_run.workflow_type,
    }


def handle_general_product_question(workflow_run: WorkflowRunResponse) -> dict:
    print("Running general product question workflow...")
    print(f"Workflow input: {workflow_run.workflow_input}")
    time.sleep(2)
    return {
        "message": "General product question workflow completed.",
        "workflow_type": workflow_run.workflow_type,
    }


WORKFLOW_HANDLERS = {
    "STOCK_DATA_ISSUE": handle_stock_data_issue,
    "WATCHLIST_BUG": handle_watchlist_bug,
    "PRICE_ALERT_BUG": handle_price_alert_bug,
    "GENERAL_PRODUCT_QUESTION": handle_general_product_question,
}

#实际根据 workflow_type 动态调用不同的处理器，如果不存在则抛出异常
def run_workflow_handler(workflow_run: WorkflowRunResponse) -> dict:
    handler = WORKFLOW_HANDLERS.get(workflow_run.workflow_type)

    if handler is None:
        raise ValueError(f"No handler found for workflow type: {workflow_run.workflow_type}")

    return handler(workflow_run)
