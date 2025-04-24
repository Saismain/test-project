from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class DeviceCreate(BaseModel):
    device_id: str
    owner: Optional[str] = None

class Device(BaseModel):
    id: int
    device_id: str
    owner: Optional[str] = None

    class Config:
        orm_mode = True

class StatCreate(BaseModel):
    x: float
    y: float
    z: float

class StatResponse(BaseModel):
    id: int
    device_id: int
    timestamp: datetime
    x: float
    y: float
    z: float

    class Config:
        orm_mode = True

class AnalysisResult(BaseModel):
    min: float
    max: float
    count: int
    sum: float
    median: float

class DeviceAnalysis(BaseModel):
    x: AnalysisResult
    y: AnalysisResult
    z: AnalysisResult

class UserAnalysis(BaseModel):
    device_id: str
    task_id: str

class AnalysisRequest(BaseModel):
    start_time: datetime
    end_time: datetime