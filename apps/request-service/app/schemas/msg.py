from pydantic import BaseModel


class HealthCheck(BaseModel):
    status: str
    environment: str
    version: str = "0.1.0"
