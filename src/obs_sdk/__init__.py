from obs_sdk.config import load_config
from obs_sdk.exporters import setup_exporters
from obs_sdk.processors import setup_span_processors

def init_observability(service_name: str = None):
    """Initialize OpenTelemetry observability for the app."""
    config = load_config()
    if service_name:
        config["service_name"] = service_name

    # Set up tracer provider and exporters
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider

    trace.set_tracer_provider(TracerProvider())
    tracer_provider = trace.get_tracer_provider()

    # Add exporters based on config
    setup_exporters(tracer_provider, config)

    # Add span processors (e.g., BatchSpanProcessor)
    setup_span_processors(tracer_provider, config)

    return tracer_provider