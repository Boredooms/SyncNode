"""
SyncNode Backend — configuration and settings.

All configuration is loaded from environment variables (via .env file).
Never put secrets directly in source code.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class SyncNodeSettings(BaseSettings):
    """Central settings object for the SyncNode backend and AI/ML layers.

    Loaded from environment variables; falls back to .env in the project root.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # ------------------------------------------------------------------ #
    # Model / Ollama                                                        #
    # ------------------------------------------------------------------ #
    ollama_base_url: str = Field(
        default="http://127.0.0.1:11434",
        description="Ollama server base URL — must be loopback/local.",
    )
    syncnode_model_id: str = Field(
        default="gemma4:e4b",
        description="Exact Ollama model tag to use for inference.",
    )
    syncnode_model_provider: Literal["ollama"] = Field(
        default="ollama",
        description="Inference provider. Only 'ollama' is allowed in Phase 1.",
    )
    syncnode_model_timeout: int = Field(
        default=120,
        description="Model call timeout in seconds.",
    )
    syncnode_model_repair_attempts: int = Field(
        default=2,
        description="Max structured-output JSON repair attempts after the initial "
        "generation (Invariant MG-03: repairs may not exceed two).",
    )

    # ------------------------------------------------------------------ #
    # Local runtime / GPU offload (RTX 2050 optimized — see              #
    # docs/INFERENCE_OPTIMIZATION.md for the measured basis).            #
    # ------------------------------------------------------------------ #
    syncnode_gpu_layers: int = Field(
        default=99,
        description=(
            "Number of model layers to offload to the GPU (Ollama num_gpu). "
            "99 = offload all layers. On the 4GB RTX 2050 the Q4_K_M gemma4:e4b "
            "weights + KV cache fit fully in VRAM at bounded context, which is "
            "~3.8x faster than Ollama's conservative auto-offload. Set to 0 to "
            "force CPU-only."
        ),
    )
    syncnode_num_ctx: int = Field(
        default=8192,
        description=(
            "Default context window (Ollama num_ctx). Bounded well below the "
            "model's 131072 max: a huge KV allocation makes Ollama fall back to "
            "CPU and inflates load time. 8192 keeps the whole model GPU-resident "
            "with headroom on 4GB VRAM (measured stable up to 32768)."
        ),
    )
    syncnode_keep_alive: str = Field(
        default="30m",
        description=(
            "Ollama keep_alive: how long the model stays resident after a request. "
            "Keeping it warm avoids the ~11-19s cold reload between workflow steps "
            "(warm reload measured at 0.01s). Use '0' to unload immediately."
        ),
    )

    # ------------------------------------------------------------------ #
    # Database                                                              #
    # ------------------------------------------------------------------ #
    database_url: str = Field(
        default="sqlite+aiosqlite:///./data/syncnode.db",
        description="SQLAlchemy async database URL.",
    )

    # ------------------------------------------------------------------ #
    # ChromaDB / RAG                                                        #
    # ------------------------------------------------------------------ #
    chroma_persist_dir: str = Field(
        default="./data/rag_index",
        description="Directory for ChromaDB persistent vector store.",
    )
    syncnode_rag_collection: str = Field(
        default="syncnode_knowledge",
        description="ChromaDB collection name for knowledge retrieval.",
    )
    syncnode_embedding_model: str = Field(
        default="all-MiniLM-L6-v2",
        description="SentenceTransformer model name for local embeddings.",
    )
    syncnode_knowledge_root: Path = Field(
        default=Path("C:/syncnode/knowledge"),
        description="Root directory of the local Markdown knowledge base.",
    )

    # ------------------------------------------------------------------ #
    # Workspace                                                             #
    # ------------------------------------------------------------------ #
    syncnode_workspace_root: Path = Field(
        default=Path("C:/syncnode/workspace"),
        description="Root of all SyncNode managed workspaces.",
    )
    syncnode_demo_workspace: Path = Field(
        default=Path("C:/syncnode/workspace/demo"),
        description="Demo workspace directory.",
    )
    syncnode_demo_document: str = Field(
        default="SyncNode_Verifier_Demo.docx",
        description="Name of the golden demo DOCX file.",
    )

    # ------------------------------------------------------------------ #
    # Demo / Test                                                           #
    # ------------------------------------------------------------------ #
    syncnode_demo_recipient: str = Field(
        default="demo@example.com",
        description="Email address used in the golden demo draft.",
    )
    syncnode_demo_failure: str = Field(
        default="none",
        description="Failure injection mode (none | false_model_success_claim | ...).",
    )

    # ------------------------------------------------------------------ #
    # FastAPI                                                               #
    # ------------------------------------------------------------------ #
    syncnode_api_host: str = Field(default="127.0.0.1")
    syncnode_api_port: int = Field(default=8000)
    syncnode_debug: bool = Field(default=True)

    # ------------------------------------------------------------------ #
    # Audit                                                                 #
    # ------------------------------------------------------------------ #
    syncnode_audit_chain: Literal["sha256"] = Field(default="sha256")

    # ------------------------------------------------------------------ #
    # Browser (Playwright)                                                  #
    # ------------------------------------------------------------------ #
    syncnode_browser_type: Literal["chromium", "firefox", "webkit"] = Field(
        default="chromium"
    )
    syncnode_browser_headless: bool = Field(default=False)
    syncnode_mail_compose_url: str = Field(
        default="",
        description=(
            "Local mail-compose page used by the golden demo browser leg. When "
            "set, navigation to a webmail/compose URL is redirected here so the "
            "draft is created against a real local DOM without external mail auth. "
            "Empty = no redirect (navigate to the requested URL verbatim)."
        ),
    )

    # ------------------------------------------------------------------ #
    # Logging                                                               #
    # ------------------------------------------------------------------ #
    syncnode_log_level: str = Field(default="INFO")
    syncnode_log_format: Literal["json", "console"] = Field(default="console")

    # ------------------------------------------------------------------ #
    # Policy                                                                #
    # ------------------------------------------------------------------ #
    syncnode_approval_required: str = Field(
        default="EXTERNAL_COMMUNICATION,DESTRUCTIVE_LOCAL",
        description="Comma-separated risk classes requiring human approval.",
    )

    @field_validator("ollama_base_url")
    @classmethod
    def must_be_local(cls, v: str) -> str:
        """Enforce that Ollama URL is local-only (loopback or unix socket)."""
        allowed = ("http://127.0.0.1", "http://localhost", "http://[::1]", "unix://")
        if not any(v.startswith(p) for p in allowed):
            raise ValueError(
                f"OLLAMA_BASE_URL must be a loopback address. Got: {v!r}. "
                "SyncNode enforces local-only inference (Invariant MG-01)."
            )
        return v

    @property
    def approval_required_set(self) -> set[str]:
        return {x.strip() for x in self.syncnode_approval_required.split(",") if x.strip()}


# Module-level singleton — import this everywhere.
settings = SyncNodeSettings()
