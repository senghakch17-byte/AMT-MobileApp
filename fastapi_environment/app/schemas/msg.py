from pydantic import BaseModel, ConfigDict


class Message(BaseModel):
    message: str

    model_config = ConfigDict(from_attributes=True)


class HealthCheck(BaseModel):
    status: str
    environment: str
    version: str = "0.1.0"