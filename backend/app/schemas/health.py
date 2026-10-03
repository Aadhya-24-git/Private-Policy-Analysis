from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class DatabaseHealth(BaseModel):
    status: str = Field(description="Connection status: 'connected' or 'disconnected'")
    pgvector_installed: bool = Field(default=False, description="Whether pgvector extension is active")
    pgvector_version: Optional[str] = Field(default=None, description="Installed pgvector version")
    error: Optional[str] = Field(default=None, description="Diagnostic error message if disconnected")


class AIConfigSummary(BaseModel):
    provider: str = Field(description="Configured active AI provider (e.g. openai, anthropic, ollama, local_qwen)")
    model: str = Field(description="Model identifier")
    embedding_provider: str = Field(description="Embedding provider identifier")


class HealthResponse(BaseModel):
    status: str = Field(default="healthy", description="Application health status")
    app_name: str = Field(description="Name of the application")
    environment: str = Field(description="Deployment environment")
    version: str = Field(default="0.1.0", description="API version")
    timestamp: datetime = Field(description="Current server UTC timestamp")
    database: DatabaseHealth = Field(description="PostgreSQL and pgvector health details")
    ai_subsystem: AIConfigSummary = Field(description="Modular AI subsystem configuration status")
