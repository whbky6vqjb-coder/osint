import os
from pydantic import BaseModel

class Settings(BaseModel):
    PROJECT_NAME: str = "Autonomous OSINT & Deep Research 24/7"
    API_V1_STR: str = "/api"
    
    # 4 vCPU & Hardware Concurrency Limits
    MAX_VCPU_WORKERS: int = int(os.getenv("MAX_VCPU_WORKERS", "4"))
    ASYNC_SEMAPHORE_LIMIT: int = 4
    
    # Storage & DB Paths
    STORAGE_DIR: str = os.getenv("STORAGE_DIR", "storage")
    DB_PATH: str = os.getenv("DB_PATH", "storage/database.sqlite")
    
    # SQLite 4 vCPU & Memory Cache Limits
    SQLITE_CACHE_SIZE_MB: int = 16  # 16MB max RAM cache
    SQLITE_MMAP_SIZE_MB: int = 256  # 256MB zero-copy mmap
    
    # LLM & Inference Engine (Nemotron-3-Nano Mamba+MoE config)
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "nemotron_local")  # nemotron_local, openai, mock
    LLM_API_BASE: str = os.getenv("LLM_API_BASE", "http://localhost:8080/v1")  # llama-server / KTransformers endpoint
    LLM_MODEL: str = os.getenv("LLM_MODEL", "nvidia/nemotron-3-nano-30b-gguf")
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "sk-no-key-required")
    MAX_CONTEXT_TOKENS: int = 1000000  # 1M Context Window
    
    # KV Cache Compression Params
    TURBOQUANT_ENABLED: bool = True
    KV_CACHE_BITS_K: int = 8  # q8_0
    KV_CACHE_BITS_V: int = 4  # q4_0
    
    # 24/7 Cloud Sync
    KAGGLE_DATASET_NAME: str = os.getenv("KAGGLE_DATASET_NAME", "osint-agent-state")
    KAGGLE_USERNAME: str = os.getenv("KAGGLE_USERNAME", "")
    KAGGLE_KEY: str = os.getenv("KAGGLE_KEY", "")

settings = Settings()
