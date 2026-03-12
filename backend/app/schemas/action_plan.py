from pydantic import BaseModel


class ActionPlanItem(BaseModel):
    domain: str
    action: str
    reason: str


class ActionPlanResponse(BaseModel):
    weekly_plan: list[ActionPlanItem]
