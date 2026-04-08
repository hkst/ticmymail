from fastapi import APIRouter, HTTPException
from tmm.config.loader import ConfigLoader
from tmm.adapters.jira_client import JiraClient
from tmm.service.errors import AppError

router = APIRouter()

@router.post("/integrations/jira/tickets")
async def create_jira_ticket(summary: str, description: str, priority: str = None):
    loader = ConfigLoader()
    jira_config = loader.jira()
    if not jira_config.get("enabled", False):
        raise HTTPException(status_code=400, detail="Jira integration disabled")

    client = JiraClient(jira_config)
    try:
        result = client.create_ticket(summary, description, priority=priority)
        return {"status": "created", "issue_key": result["issueKey"]}
    except Exception as e:
        raise AppError("JIRA_REQUEST_FAILED", str(e), status_code=500)

