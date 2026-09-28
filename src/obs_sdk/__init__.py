import atexit
import logging
from contextlib import contextmanager
from typing import Optional, Sequence, Union, Dict, Any, Generator

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider, SpanProcessor
from opentelemetry.sdk.resources import Resource, SERVICE_NAME

from obs_sdk.config import load_config
from obs_sdk.exporters import setup_exporters, create_otlp_exporter
from obs_sdk.processors import setup_span_processors
from obs_sdk.instrumentation import setup_auto_instrumentation

logger = logging.getLogger(__name__)

_ACTIVE_PROVIDER: Optional[TracerProvider] = None
_ATEXIT_REGISTERED: bool = False


def init_observability(
    service_name: Optional[str] = None,
    *,
    protocol: Optional[str] = None,
    auto_instrument: Optional[bool] = None,
    instrumentations: Optional[Sequence[Union[str, Any]]] = None,
    resource_attributes: Optional[Dict[str, Any]] = None,
    resource: Optional[Resource] = None,
    span_processors: Optional[Sequence[SpanProcessor]] = None,
    register_atexit: bool = True,
    config: Optional[Dict[str, Any]] = None,
) -> TracerProvider:
    """Initialize OpenTelemetry observability for the app.

    Args:
        service_name: Name of the service to attach to the OTel Resource.
        protocol: Export protocol ('http' or 'grpc'). Defaults to config or 'http'.
        auto_instrument: Whether to enable auto-instrumentation. Defaults to config (True).
        instrumentations: Configurable list of instrumentations to enable
                          (e.g., ['requests', 'redis']). If None, uses default list.
        resource_attributes: Additional attributes to add to the OTel Resource.
        resource: An existing OTel Resource instance to merge with.
        span_processors: Additional custom SpanProcessor instances to add to TracerProvider.
        register_atexit: Whether to register an atexit hook to flush and shut down on process exit.
        config: Optional configuration dict overriding load_config().

    Returns:
        The configured TracerProvider instance.
    """
    cfg = dict(load_config()) if config is None else dict(config)
    if protocol:
        cfg["protocol"] = protocol
    if service_name:
        cfg["service_name"] = service_name
    else:
        service_name = cfg.get("service_name", "unknown-service")

    # Set up OTel Resource with service name as an attribute
    attrs = {SERVICE_NAME: service_name}
    if resource_attributes:
        attrs.update(resource_attributes)
    base_resource = Resource.create(attrs)
    final_resource = resource.merge(base_resource) if resource is not None else base_resource

    # Create TracerProvider with the configured resource
    tracer_provider = TracerProvider(resource=final_resource)
    trace.set_tracer_provider(tracer_provider)

    # Set up exporters based on config (each exporter adds its own BatchSpanProcessor)
    setup_exporters(tracer_provider, cfg)

    # Set up additional span processors if configured or provided
    setup_span_processors(tracer_provider, config=cfg, processors=span_processors)

    # Auto-instrumentation with configurable list
    should_instrument = (
        auto_instrument if auto_instrument is not None else cfg.get("auto_instrument", True)
    )
    if should_instrument:
        inst_list = (
            instrumentations
            if instrumentations is not None
            else cfg.get("instrumentations")
        )
        setup_auto_instrumentation(instrumentations=inst_list)

    # Register lifecycle tracking and atexit hook
    global _ACTIVE_PROVIDER, _ATEXIT_REGISTERED
    _ACTIVE_PROVIDER = tracer_provider

    if register_atexit and not _ATEXIT_REGISTERED:
        atexit.register(_atexit_handler)
        _ATEXIT_REGISTERED = True

    return tracer_provider


def force_flush(
    timeout_millis: int = 30000,
    provider: Optional[TracerProvider] = None,
) -> bool:
    """Force flush all spans in the provider.

    Useful for short-lived CLI runs or batch jobs to ensure all pending
    spans are exported before execution proceeds or exits.

    Returns:
        True if all processors flushed successfully within the timeout, False otherwise.
    """
    tp = provider or _ACTIVE_PROVIDER
    if tp is None:
        current = trace.get_tracer_provider()
        if isinstance(current, TracerProvider):
            tp = current
    if tp is not None and hasattr(tp, "force_flush"):
        try:
            return bool(tp.force_flush(timeout_millis=timeout_millis))
        except Exception as e:
            logger.warning("Error during provider force_flush: %s", e)
            return False
    return True


def shutdown(provider: Optional[TracerProvider] = None) -> None:
    """Shut down the provider and its span processors.

    Flushes all remaining spans and cleans up resources.
    """
    global _ACTIVE_PROVIDER
    tp = provider or _ACTIVE_PROVIDER
    if tp is None:
        current = trace.get_tracer_provider()
        if isinstance(current, TracerProvider):
            tp = current
    if tp is not None and hasattr(tp, "shutdown"):
        try:
            tp.shutdown()
        except Exception as e:
            logger.warning("Error during provider shutdown: %s", e)
    if tp is _ACTIVE_PROVIDER:
        _ACTIVE_PROVIDER = None


def _atexit_handler() -> None:
    """Automatically flush and shut down active provider on process exit."""
    try:
        force_flush()
        shutdown()
    except Exception as e:
        logger.warning("Error during atexit observability shutdown: %s", e)


@contextmanager
def observability_lifecycle(
    service_name: Optional[str] = None,
    timeout_millis: int = 30000,
    **kwargs: Any,
) -> Generator[TracerProvider, None, None]:
    """Context manager for short-lived CLI runs or batch jobs.

    Initializes observability on enter, and guarantees force_flush() and shutdown()
    on exit (even if exceptions occur).

    Example:
        with observability_lifecycle("my-cli"):
            run_cli_command()
    """
    provider = init_observability(service_name=service_name, **kwargs)
    try:
        yield provider
    finally:
        force_flush(timeout_millis=timeout_millis, provider=provider)
        shutdown(provider=provider)


# Aliases for explicit naming
flush_observability = force_flush
shutdown_observability = shutdown

__all__ = [
    "init_observability",
    "force_flush",
    "shutdown",
    "flush_observability",
    "shutdown_observability",
    "observability_lifecycle",
    "load_config",
    "setup_exporters",
    "create_otlp_exporter",
    "setup_span_processors",
    "setup_auto_instrumentation",
]