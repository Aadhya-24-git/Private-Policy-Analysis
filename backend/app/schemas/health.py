from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class DatabaseHealth(BaseModel):
    status: str = Field(description="Connection status: 'connected' or 'disconnected'")
    pgvector_installed: bool = Field(default=False, description="Whether pgvector extension is active")
    pgvector_version: Optional[str] = Field(default=None, description="Installed pgvector version")
    error: Optional[str] = Field(default=None, description="Diagnostic error message if disconnected")


class OllamaDiagnostics(BaseModel):
    reachable: bool = Field(default=False, description="Whether Ollama daemon is reachable")
    base_url: str = Field(description="Configured Ollama base URL")
    chat_model: str = Field(description="Configured chat model identifier")
    chat_model_available: bool = Field(default=False, description="Whether configured chat model is installed in Ollama")
    embedding_model: str = Field(description="Configured embedding model identifier")
    embedding_model_available: bool = Field(default=False, description="Whether configured embedding model is installed in Ollama")
    available_models: List[str] = Field(default_factory=list, description="List of all model tags found in Ollama")
    error: Optional[str] = Field(default=None, description="Diagnostic error message if unreachable")


class AIConfigSummary(BaseModel):
    provider: str = Field(description="Configured active AI provider (e.g. ollama, openai, anthropic, local_qwen)")
    model: str = Field(description="Model identifier")
    embedding_provider: str = Field(description="Embedding provider identifier")
    embedding_model: Optional[str] = Field(default=None, description="Embedding model identifier")
    embedding_dimension: Optional[int] = Field(default=None, description="Vector dimension of embeddings")
    ollama_diagnostics: Optional[OllamaDiagnostics] = Field(default=None, description="Ollama connectivity and model diagnostics")


class HealthResponse(BaseModel):
    status: str = Field(default="healthy", description="Application health status")
    app_name: str = Field(description="Name of the application")
    environment: str = Field(description="Deployment environment")
    version: str = Field(default="0.1.0", description="API version")
    timestamp: datetime = Field(description="Current server UTC timestamp")
    database: DatabaseHealth = Field(description="PostgreSQL and pgvector health details")
    ai_subsystem: AIConfigSummary = Field(description="Modular AI subsystem configuration status")
