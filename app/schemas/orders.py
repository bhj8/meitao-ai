from pydantic import BaseModel

class PlanNameResponse(BaseModel):
    plan_name: str
