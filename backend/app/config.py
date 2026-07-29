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
    
    # Self-Hosted LLM Engine (Qwen3.6-12B IQ-Ultra-Heretic GGUF)
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "qwen_local")
    LLM_API_BASE: str = os.getenv("LLM_API_BASE", "http://localhost:8080/v1")  # Self-hosted llama-server
    LLM_MODEL: str = os.getenv("LLM_MODEL", "KevinJK51/Qwen3.6-12B-IQ-Ultra-Heretic-Uncensored-Thinking-V2-Hightop-GGUF")
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "sk-no-key-required")
    MAX_CONTEXT_TOKENS: int = 1000000  # 1M Context Window
    
    # llama-server Hardware & KV Cache Optimizations
    LLAMA_SERVER_FLAGS: str = "--mmap --mlock --cache-type-k q4_0 --cache-type-v q4_0 --flash-attn -b 512 -ub 256 -t 2"
    
    # 24/7 Cloud Sync
    KAGGLE_DATASET_NAME: str = os.getenv("KAGGLE_DATASET_NAME", "osint-agent-state")
    KAGGLE_USERNAME: str = os.getenv("KAGGLE_USERNAME", "")
    KAGGLE_KEY: str = os.getenv("KAGGLE_KEY", "")

settings = Settings()
