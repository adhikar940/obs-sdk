import importlib
import inspect
import logging
from typing import Optional, Sequence, Union, Any, List, Callable, Dict

logger = logging.getLogger(__name__)

DEFAULT_INSTRUMENTATIONS = (
    "requests",
    "httpx",
    "urllib",
    "urllib3",
    "aiohttp",
    "postgres",
    "psycopg2",
    "redis",
    "dbapi",
)


def _instrument_requests() -> None:
    from opentelemetry.instrumentation.requests import RequestsInstrumentor
    RequestsInstrumentor().instrument()


def _instrument_httpx() -> None:
    from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
    HTTPXClientInstrumentor().instrument()


def _instrument_urllib() -> None:
    instrumented = False
    last_err = None
    try:
        from opentelemetry.instrumentation.urllib import URLLibInstrumentor
        URLLibInstrumentor().instrument()
        instrumented = True
    except Exception as e:
        last_err = e
    try:
        from opentelemetry.instrumentation.urllib3 import URLLib3Instrumentor
        URLLib3Instrumentor().instrument()
        instrumented = True
    except Exception as e:
        if last_err is None:
            last_err = e
    if not instrumented:
        raise last_err or ImportError("Neither opentelemetry.instrumentation.urllib nor urllib3 found")


def _instrument_urllib3() -> None:
    from opentelemetry.instrumentation.urllib3 import URLLib3Instrumentor
    URLLib3Instrumentor().instrument()


def _instrument_aiohttp() -> None:
    instrumented = False
    last_err = None
    try:
        from opentelemetry.instrumentation.aiohttp_client import AioHttpClientInstrumentor
        AioHttpClientInstrumentor().instrument()
        instrumented = True
    except Exception as e:
        last_err = e
    try:
        from opentelemetry.instrumentation.aiohttp_server import AioHttpServerInstrumentor
        AioHttpServerInstrumentor().instrument()
        instrumented = True
    except Exception:
        pass
    if not instrumented:
        raise last_err or ImportError("No opentelemetry.instrumentation.aiohttp_client found")


def _instrument_postgres() -> None:
    instrumented = False
    last_err = None
    # 1. Try psycopg2
    try:
        from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor
        Psycopg2Instrumentor().instrument()
        instrumented = True
    except Exception as e:
        last_err = e
    # 2. Try psycopg (psycopg3)
    try:
        from opentelemetry.instrumentation.psycopg import PsycopgInstrumentor
        PsycopgInstrumentor().instrument()
        instrumented = True
    except Exception as e:
        if last_err is None:
            last_err = e
    # 3. Try asyncpg
    try:
        from opentelemetry.instrumentation.asyncpg import AsyncPGInstrumentor
        AsyncPGInstrumentor().instrument()
        instrumented = True
    except Exception as e:
        if last_err is None:
            last_err = e

    if not instrumented:
        raise last_err or ImportError("No PostgreSQL instrumentor (psycopg2, psycopg, or asyncpg) found")


def _instrument_psycopg2() -> None:
    from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor
    Psycopg2Instrumentor().instrument()


def _instrument_psycopg() -> None:
    from opentelemetry.instrumentation.psycopg import PsycopgInstrumentor
    PsycopgInstrumentor().instrument()


def _instrument_asyncpg() -> None:
    from opentelemetry.instrumentation.asyncpg import AsyncPGInstrumentor
    AsyncPGInstrumentor().instrument()


def _instrument_redis() -> None:
    from opentelemetry.instrumentation.redis import RedisInstrumentor
    RedisInstrumentor().instrument()


def _instrument_dbapi() -> None:
    from opentelemetry.instrumentation.dbapi import trace_integration
    trace_integration(enable=True)


KNOWN_INSTRUMENTORS: Dict[str, Callable[[], None]] = {
    "requests": _instrument_requests,
    "httpx": _instrument_httpx,
    "urllib": _instrument_urllib,
    "urllib3": _instrument_urllib3,
    "urlibb": _instrument_urllib,  # Alias for common typo
    "aiohttp": _instrument_aiohttp,
    "aiohttp_client": _instrument_aiohttp,
    "aiohttp-client": _instrument_aiohttp,
    "postgres": _instrument_postgres,
    "postgresql": _instrument_postgres,
    "postgress": _instrument_postgres,  # Alias for user's typo
    "psycopg2": _instrument_psycopg2,
    "psycopg": _instrument_psycopg,
    "asyncpg": _instrument_asyncpg,
    "redis": _instrument_redis,
    "dbapi": _instrument_dbapi,
}


def _instrument_single(item: Union[str, Any]) -> None:
    """Instrument a single library by name, class, or instance."""
    if isinstance(item, str):
        key = item.strip().lower()
        if key in KNOWN_INSTRUMENTORS:
            KNOWN_INSTRUMENTORS[key]()
            return

        # Attempt dynamic import: e.g. opentelemetry.instrumentation.<key>
        mod_name = f"opentelemetry.instrumentation.{key}"
        mod = importlib.import_module(mod_name)
        
        target_name = f"{key}instrumentor"
        instrumentor_cls = None

        # Look for exact class name match first (e.g. FastAPIInstrumentor)
        for attr in dir(mod):
            if attr.lower() == target_name:
                candidate = getattr(mod, attr)
                if isinstance(candidate, type) and not inspect.isabstract(candidate) and hasattr(candidate, "instrument"):
                    instrumentor_cls = candidate
                    break

        # Fallback to any non-abstract class ending with Instrumentor except BaseInstrumentor
        if instrumentor_cls is None:
            for attr in dir(mod):
                if attr.endswith("Instrumentor") and attr != "BaseInstrumentor":
                    candidate = getattr(mod, attr)
                    if isinstance(candidate, type) and not inspect.isabstract(candidate) and hasattr(candidate, "instrument"):
                        instrumentor_cls = candidate
                        break

        if instrumentor_cls:
            instrumentor_cls().instrument()
        elif hasattr(mod, "instrument"):
            mod.instrument()
        else:
            raise ValueError(f"No Instrumentor found in module {mod_name}")
    elif hasattr(item, "instrument") and callable(getattr(item, "instrument")):
        if isinstance(item, type):
            item().instrument()
        else:
            item.instrument()
    elif callable(item):
        item()
    else:
        raise TypeError(f"Unsupported instrumentation target: {item}")


def setup_auto_instrumentation(
    instrumentations: Optional[Sequence[Union[str, Any]]] = None,
    fail_on_error: bool = False,
) -> List[str]:
    """Enable auto-instrumentation for configured libraries.

    Args:
        instrumentations: Configurable list/sequence of instrumentation names
                         (e.g., ['requests', 'redis', 'postgres']), classes, or instances.
                         If None, defaults to DEFAULT_INSTRUMENTATIONS.
                         If an empty sequence, no instrumentations are enabled.
        fail_on_error: If True, raises exceptions when an instrumentor fails.
                       If False (default), logs a warning and proceeds.

    Returns:
        List of successfully enabled instrumentation names or representations.
    """
    if instrumentations is None:
        targets = list(DEFAULT_INSTRUMENTATIONS)
    else:
        targets = list(instrumentations)

    enabled: List[str] = []
    for item in targets:
        try:
            _instrument_single(item)
            name = item if isinstance(item, str) else getattr(item, "__name__", str(item))
            enabled.append(str(name))
            logger.debug("Successfully enabled auto-instrumentation for %s", name)
        except Exception as e:
            if fail_on_error:
                raise
            logger.warning("Could not enable auto-instrumentation for '%s': %s", item, e)

    return enabled