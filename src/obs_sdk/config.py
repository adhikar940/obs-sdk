import os
from typing import Dict, Any

def load_config() -> Dict[str, Any]:
    """Load observability config from environment variables."""
    return {
        "service_name": os.getenv("OTEL_SERVICE_NAME", "unknown-service"),
        "local_langfuse_export": os.getenv("LOCAL_LANGfUSE_EXPORT", "false").lower() == "true",
        "remote_langfuse_export": os.getenv("REMOTE_LANGfUSE_EXPORT", "false").lower() == "true",
        "console_export": os.getenv("CONSOLE_EXPORT", "false").lower() == "true",
        "local_langfuse_endpoint": os.getenv("LOCAL_LANGfUSE_ENDPOINT", "http://localhost:4317"),
        "remote_langfuse_endpoint": os.getenv("REMOTE_LANGfUSE_ENDPOINT"),
        "remote_langfuse_api_key": os.getenv("REMOTE_LANGfUSE_API_KEY"),
    }