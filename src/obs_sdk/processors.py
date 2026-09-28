import logging
from typing import Optional, Sequence, Union, Dict, Any
from opentelemetry.sdk.trace import SpanProcessor

logger = logging.getLogger(__name__)


def setup_span_processors(
    tracer_provider,
    config: Optional[Dict[str, Any]] = None,
    processors: Optional[Sequence[SpanProcessor]] = None,
) -> None:
    """Set up additional span processors (e.g., for custom filtering, sampling, or metrics).

    Note: Exporter setup already creates and attaches BatchSpanProcessor instances
    for each configured exporter (Langfuse, Console, etc.). This function handles
    any extra custom SpanProcessor instances provided via config or parameters.
    """
    to_add = []

    if isinstance(config, dict):
        custom = config.get("span_processors") or config.get("processors")
        if custom:
            if isinstance(custom, (list, tuple, set)):
                to_add.extend(custom)
            else:
                to_add.append(custom)
    elif config is not None:
        if isinstance(config, (list, tuple, set)):
            to_add.extend(config)
        else:
            to_add.append(config)

    if processors:
        to_add.extend(processors)

    for processor in to_add:
        try:
            tracer_provider.add_span_processor(processor)
        except Exception as e:
            logger.warning("Failed to add span processor %r: %s", processor, e)