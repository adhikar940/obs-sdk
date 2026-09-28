import logging
from typing import Optional, Dict, Any
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

logger = logging.getLogger(__name__)


def _normalize_http_endpoint(endpoint: str) -> str:
    cleaned = endpoint.rstrip("/")
    if cleaned.endswith("/v1/traces") or cleaned.endswith("/traces"):
        return cleaned
    return f"{cleaned}/v1/traces"


def create_otlp_exporter(
    endpoint: str,
    headers: Optional[Dict[str, str]] = None,
    protocol: str = "http",
):
    """Create an OTLP trace exporter for HTTP or gRPC.

    Args:
        endpoint: The target backend endpoint.
        headers: Optional HTTP headers or gRPC metadata.
        protocol: 'http' (or 'http/protobuf') or 'grpc'. Defaults to 'http'.

    Returns:
        Configured OTLPSpanExporter instance (HTTP or gRPC).
    """
    proto = (protocol or "http").lower().strip()
    if proto in ("grpc",):
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
            OTLPSpanExporter as GRPCExporter,
        )
        return GRPCExporter(
            endpoint=endpoint,
            headers=headers if headers else None,
        )
    else:
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
            OTLPSpanExporter as HTTPExporter,
        )
        return HTTPExporter(
            endpoint=_normalize_http_endpoint(endpoint),
            headers=headers if headers else None,
        )


def setup_exporters(tracer_provider, config: dict):
    """Set up exporters based on config."""
    global_protocol = config.get("protocol", "http")

    # 1. Local Langfuse
    if config.get("local_langfuse_export"):
        endpoint = config["local_langfuse_endpoint"]
        protocol = config.get("local_langfuse_protocol", global_protocol)
        headers = {}
        if config.get("local_langfuse_api_key"):
            headers["Authorization"] = f"Bearer {config['local_langfuse_api_key']}"
        local_exporter = create_otlp_exporter(
            endpoint=endpoint,
            headers=headers if headers else None,
            protocol=protocol,
        )
        tracer_provider.add_span_processor(
            BatchSpanProcessor(local_exporter)
        )

    # 2. Remote Langfuse
    if config.get("remote_langfuse_export"):
        if not config.get("remote_langfuse_endpoint"):
            raise ValueError("REMOTE_LANGFUSE_ENDPOINT must be set")
        endpoint = config["remote_langfuse_endpoint"]
        protocol = config.get("remote_langfuse_protocol", global_protocol)
        headers = {}
        if config.get("remote_langfuse_api_key"):
            headers["Authorization"] = f"Bearer {config['remote_langfuse_api_key']}"
        remote_exporter = create_otlp_exporter(
            endpoint=endpoint,
            headers=headers if headers else None,
            protocol=protocol,
        )
        tracer_provider.add_span_processor(
            BatchSpanProcessor(remote_exporter)
        )

    # 3. Arize Phoenix
    if config.get("arize_export"):
        if not config.get("arize_endpoint"):
            raise ValueError("ARIZE_ENDPOINT must be set when ARIZE_EXPORT is enabled")
        endpoint = config["arize_endpoint"]
        protocol = config.get("arize_protocol", global_protocol)
        headers = {}
        if config.get("arize_api_key"):
            headers["api_key"] = config["arize_api_key"]
            headers["Authorization"] = f"Bearer {config['arize_api_key']}"
        if config.get("arize_project_name"):
            headers["project_name"] = config["arize_project_name"]
        arize_exporter = create_otlp_exporter(
            endpoint=endpoint,
            headers=headers if headers else None,
            protocol=protocol,
        )
        tracer_provider.add_span_processor(
            BatchSpanProcessor(arize_exporter)
        )

    # 4. Console Exporter
    if config.get("console_export"):
        console_exporter = ConsoleSpanExporter()
        tracer_provider.add_span_processor(
            BatchSpanProcessor(console_exporter)
        )