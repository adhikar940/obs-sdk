from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

def setup_exporters(tracer_provider, config: dict):
    """Set up exporters based on config."""
    if config["local_langfuse_export"]:
        local_exporter = OTLPSpanExporter(
            endpoint=f"{config['local_langfuse_endpoint']}/v1/traces",
        )
        tracer_provider.add_span_processor(
            BatchSpanProcessor(local_exporter)
        )

    if config["remote_langfuse_export"]:
        if not config["remote_langfuse_endpoint"]:
            raise ValueError("REMOTE_LANGfUSE_ENDPOINT must be set")
        remote_exporter = OTLPSpanExporter(
            endpoint=f"{config['remote_langfuse_endpoint']}/v1/traces",
            headers={"Authorization": f"Bearer {config['remote_langfuse_api_key']}"},
        )
        tracer_provider.add_span_processor(
            BatchSpanProcessor(remote_exporter)
        )

    if config["console_export"]:
        console_exporter = ConsoleSpanExporter()
        tracer_provider.add_span_processor(
            BatchSpanProcessor(console_exporter)
        )