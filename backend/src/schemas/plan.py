from pydantic import BaseModel,ConfigDict,Field
class PlanCreate(BaseModel):
 model_config=ConfigDict(extra='forbid')
 case_id:str
 budget:int=Field(ge=0,le=1000000)
 costs_json:str=Field(max_length=5000)
