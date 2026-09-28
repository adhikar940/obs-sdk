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

    # Langfuse configuration
    langfuse_export = os.getenv("LANGFUSE_EXPORT", "false")
    langfuse_protocol = (os.getenv("LANGFUSE_PROTOCOL") or protocol).lower().strip()
    default_langfuse_endpoint = (
        "http://localhost:4317" if langfuse_protocol == "grpc" else "http://localhost:3000/api/public/otel"
    )
    langfuse_endpoint = os.getenv("LANGFUSE_ENDPOINT") or default_langfuse_endpoint
    langfuse_api_key = os.getenv("LANGFUSE_API_KEY")

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

    # Console
    console_export = os.getenv("CONSOLE_EXPORT", "false")

    # Auto-instrumentation
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
        "langfuse_export": str(langfuse_export).lower() == "true",
        "langfuse_endpoint": langfuse_endpoint,
        "langfuse_api_key": langfuse_api_key,
        "langfuse_protocol": langfuse_protocol,
        "arize_export": str(arize_export).lower() == "true",
        "arize_endpoint": arize_endpoint,
        "arize_api_key": arize_api_key,
        "arize_project_name": arize_project_name,
        "arize_protocol": arize_protocol,
        "console_export": str(console_export).lower() == "true",
        "auto_instrument": auto_instrument,
        "instrumentations": instrumentations,
    }