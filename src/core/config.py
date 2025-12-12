from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    database_url: str
    
    # RabbitMQ
    rabbitmq_url: str
    
    # Application
    log_level: str = "INFO"
    workers_num: int = 3
    task_timeout_seconds: int = 300
    
    class Config:
        env_file = ".env"


settings = Settings()
