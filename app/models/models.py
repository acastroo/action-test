from typing import Dict, List

from pydantic import BaseModel


class AlertOutModel(BaseModel):
    service: Dict[str, str] = []


class AlertInputModel(BaseModel):
    service: Dict[str, str]
    # resourcelabels: Dict[str, dict]


class PayloadAlertsResponseModel(BaseModel):
    payload: List[AlertOutModel] = []


class Token(BaseModel):
    access_token: str
    token_type: str
