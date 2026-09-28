import os
from typing import Dict, Any, Optional, List


def load_config() -> Dict[str, Any]:
    """Load observability config from environment variables."""
    # Global protocol: default 'http', option to switch to 'grpc'
    protocol = (
        os.getenv("OTEL_EXPORTER_OTLP_PROTOCOL")
        or os.getenv("OTLP_PROTOCOL")
        or "http"
    ).lower().strip()
    if protocol == "http/protobuf":
        protocol = "http"

    local_langfuse_export = (
        os.getenv("LOCAL_LANGFUSE_EXPORT")
        or os.getenv("LOCAL_LANGfUSE_EXPORT", "false")
    )
    remote_langfuse_export = (
        os.getenv("REMOTE_LANGFUSE_EXPORT")
        or os.getenv("REMOTE_LANGfUSE_EXPORT", "false")
    )
    console_export = os.getenv("CONSOLE_EXPORT", "false")

    local_langfuse_endpoint = (
        os.getenv("LOCAL_LANGFUSE_ENDPOINT")
        or os.getenv("LOCAL_LANGfUSE_ENDPOINT", "http://localhost:4318")
    )
    local_langfuse_api_key = (
        os.getenv("LOCAL_LANGFUSE_API_KEY")
        or os.getenv("LOCAL_LANGfUSE_API_KEY")
    )
    local_langfuse_protocol = (
        os.getenv("LOCAL_LANGFUSE_PROTOCOL")
        or protocol
    ).lower().strip()

    remote_langfuse_endpoint = (
        os.getenv("REMOTE_LANGFUSE_ENDPOINT")
        or os.getenv("REMOTE_LANGfUSE_ENDPOINT")
    )
    remote_langfuse_api_key = (
        os.getenv("REMOTE_LANGFUSE_API_KEY")
        or os.getenv("REMOTE_LANGfUSE_API_KEY")
    )
    remote_langfuse_protocol = (
        os.getenv("REMOTE_LANGFUSE_PROTOCOL")
        or protocol
    ).lower().strip()

    # Arize Phoenix configuration
    arize_export = (
        os.getenv("ARIZE_EXPORT")
        or os.getenv("PHOENIX_EXPORT", "false")
    )
    arize_protocol = (
        os.getenv("ARIZE_PROTOCOL")
        or protocol
    ).lower().strip()
    default_arize_endpoint = (
        "http://localhost:14317" if arize_protocol == "grpc" else "http://localhost:6006/v1/traces"
    )
    arize_endpoint = (
        os.getenv("ARIZE_ENDPOINT")
        or os.getenv("PHOENIX_ENDPOINT")
        or default_arize_endpoint
    )
    arize_api_key = os.getenv("ARIZE_API_KEY") or os.getenv("PHOENIX_API_KEY")
    arize_project_name = os.getenv("ARIZE_PROJECT_NAME") or os.getenv("PHOENIX_PROJECT_NAME")

    auto_instrument_raw = os.getenv("AUTO_INSTRUMENT", "true").lower()
    auto_instrument = auto_instrument_raw in ("true", "1", "yes")

    auto_instrumentations_env = os.getenv("AUTO_INSTRUMENTATIONS")
    instrumentations: Optional[List[str]] = (
        [item.strip() for item in auto_instrumentations_env.split(",") if item.strip()]
        if auto_instrumentations_env is not None
        else None
    )

    return {
        "service_name": os.getenv("OTEL_SERVICE_NAME", "unknown-service"),
        "protocol": protocol,
        "local_langfuse_export": str(local_langfuse_export).lower() == "true",
        "local_langfuse_endpoint": local_langfuse_endpoint,
        "local_langfuse_api_key": local_langfuse_api_key,
        "local_langfuse_protocol": local_langfuse_protocol,
        "remote_langfuse_export": str(remote_langfuse_export).lower() == "true",
        "remote_langfuse_endpoint": remote_langfuse_endpoint,
        "remote_langfuse_api_key": remote_langfuse_api_key,
        "remote_langfuse_protocol": remote_langfuse_protocol,
        "arize_export": str(arize_export).lower() == "true",
        "arize_endpoint": arize_endpoint,
        "arize_api_key": arize_api_key,
        "arize_project_name": arize_project_name,
        "arize_protocol": arize_protocol,
        "console_export": str(console_export).lower() == "true",
        "auto_instrument": auto_instrument,
        "instrumentations": instrumentations,
    }