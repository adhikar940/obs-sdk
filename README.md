# obs-sdk: OpenTelemetry Observability SDK

`obs-sdk` is a lightweight, batteries-included OpenTelemetry SDK wrapper designed for Python applications, microservices, and short-lived CLI tools. It provides seamless tracing to backends such as **Langfuse** (local and remote), **Arize Phoenix**, and console stdout, with automatic resource naming, protocol flexibility (HTTP or gRPC), configurable auto-instrumentation, and full lifecycle management.

---

## Features

- **Protocol Selection**: Defaults to `http` (ideal for web apps, Langfuse, and CLI runs) with seamless option to switch to `grpc`.
- **Multiple Observability Backends**: Built-in support for **Langfuse** (local & remote), **Arize Phoenix**, and console output.
- **OpenTelemetry Resource Attributes**: Automatically attaches `service.name` (and optional custom attributes) as an OpenTelemetry `Resource` attribute to all spans.
- **Batched Exporters**: Configures OTLP trace exporters paired with `BatchSpanProcessor` instances.
- **Custom Span Processors**: Extensible span processor registration without empty or unconfigured processor crashes.
- **Configurable Auto-Instrumentation**: Automatically instruments supported libraries (`requests`, `psycopg2`, `redis`, `dbapi`, etc.) with lazy module loading and configurable target lists.
- **CLI & Short-Lived Process Lifecycle**: Provides explicit `force_flush()`, `shutdown()`, an `atexit` safety handler, and an `observability_lifecycle` context manager to ensure all buffered spans are delivered before CLI processes exit.

---

## Installation

```bash
pip install .
```

Or install dependencies via `requirements.txt`:
```bash
pip install -r requirements.txt
```

---

## Environment Variables

| Variable | Description | Default |
| :--- | :--- | :--- |
| `OTEL_SERVICE_NAME` | Default service name attached to the OTel Resource (`service.name`) | `unknown-service` |
| `OTEL_EXPORTER_OTLP_PROTOCOL` | Default OTLP protocol (`http` or `grpc`) | `http` |
| `LOCAL_LANGFUSE_EXPORT` | Enable export to local Langfuse / collector (`true`/`false`) | `false` |
| `LOCAL_LANGFUSE_ENDPOINT` | Local OTLP traces endpoint | `http://localhost:4318` |
| `LOCAL_LANGFUSE_API_KEY` | Optional API key / bearer token for local exporter | None |
| `LOCAL_LANGFUSE_PROTOCOL` | Override protocol for local Langfuse (`http` or `grpc`) | Inherits global protocol |
| `REMOTE_LANGFUSE_EXPORT` | Enable export to remote Langfuse (`true`/`false`) | `false` |
| `REMOTE_LANGFUSE_ENDPOINT` | Remote Langfuse OTLP endpoint (e.g. `https://cloud.langfuse.com/api/public/otel`) | None |
| `REMOTE_LANGFUSE_API_KEY` | Remote Langfuse API key / bearer token | None |
| `REMOTE_LANGFUSE_PROTOCOL` | Override protocol for remote Langfuse (`http` or `grpc`) | Inherits global protocol |
| `ARIZE_EXPORT` | Enable export to Arize Phoenix (`true`/`false`) | `false` |
| `ARIZE_ENDPOINT` | Arize Phoenix OTLP endpoint | HTTP: `http://localhost:6006/v1/traces`, gRPC: `http://localhost:14317` |
| `ARIZE_PROTOCOL` | Protocol for Arize Phoenix (`http` or `grpc`) | Inherits global protocol |
| `ARIZE_API_KEY` | Optional API key for Arize Cloud or protected Phoenix | None |
| `ARIZE_PROJECT_NAME` | Optional project name header for Arize Phoenix | None |
| `CONSOLE_EXPORT` | Enable console span exporter (`true`/`false`) | `false` |
| `AUTO_INSTRUMENT` | Enable auto-instrumentation (`true`/`false`) | `true` |
| `AUTO_INSTRUMENTATIONS` | Comma-separated list of libraries to instrument (e.g. `requests,redis`) | `requests,psycopg2,redis,dbapi` |

---

## Usage

### 1. Protocol: HTTP vs gRPC

`obs-sdk` defaults to `http` for maximum compatibility with web endpoints like Langfuse. You can switch to `grpc` globally or per backend:

Via environment variable:
```env
OTEL_EXPORTER_OTLP_PROTOCOL="grpc"
```

Or programmatically:
```python
from obs_sdk import init_observability

# Use gRPC protocol
provider = init_observability("my-service", protocol="grpc")
```

### 2. Exporting to Arize Phoenix

To send traces to Arize Phoenix, enable `ARIZE_EXPORT=true`:

In `.env`:
```env
ARIZE_EXPORT=true
ARIZE_ENDPOINT="http://localhost:6006/v1/traces"  # Or "http://localhost:14317" for gRPC
ARIZE_PROTOCOL="http"                             # Or "grpc"
```

Or programmatically:
```python
from obs_sdk import init_observability

provider = init_observability(
    "my-llm-service",
    config={
        "arize_export": True,
        "arize_endpoint": "http://localhost:6006/v1/traces",
        "arize_protocol": "http",  # or 'grpc' with "http://localhost:14317"
    },
)
```

### 3. Short-Lived CLI Commands & Scripts

For CLI tools or batch jobs that execute quickly and exit, use the `observability_lifecycle` context manager. It guarantees that pending spans are flushed and processors are shut down cleanly before process exit.

```python
from obs_sdk import observability_lifecycle
from opentelemetry import trace

def run_cli():
    with observability_lifecycle("my-cli-tool"):
        tracer = trace.get_tracer(__name__)
        with tracer.start_as_current_span("cli_command"):
            print("Executing CLI task...")

if __name__ == "__main__":
    run_cli()
```

Alternatively, call `force_flush()` and `shutdown()` manually:

```python
from obs_sdk import init_observability, force_flush, shutdown
from opentelemetry import trace

provider = init_observability(service_name="my-cli-tool")
tracer = trace.get_tracer(__name__)

with tracer.start_as_current_span("task"):
    print("Doing work...")

# Flush and shutdown before exit
force_flush()
shutdown()
```

### 4. Configurable Auto-Instrumentation

By default, `init_observability` enables auto-instrumentation for common libraries (`requests`, `psycopg2`, `redis`, `dbapi`). You can specify exactly which libraries to instrument:

```python
from obs_sdk import init_observability

# Instrument only requests and redis
provider = init_observability(
    service_name="web-scraper",
    instrumentations=["requests", "redis"],
)

# Disable auto-instrumentation entirely
provider = init_observability(
    service_name="manual-only-service",
    auto_instrument=False,
)
```

### 5. Resource Attributes

The service name is attached to the OpenTelemetry Resource attribute `service.name`. Additional resource attributes can also be supplied:

```python
provider = init_observability(
    service_name="order-service",
    resource_attributes={
        "deployment.environment": "production",
        "service.version": "2.4.0",
        "host.name": "worker-node-01",
    },
)

# Verify resource attributes
print(provider.resource.attributes["service.name"])  # 'order-service'
print(provider.resource.attributes["deployment.environment"])  # 'production'
```

### 6. Custom Span Processors

Exporters already configure their own `BatchSpanProcessor` instances. To add custom processors (e.g., for filtering, sampling, or metrics):

```python
from opentelemetry.sdk.trace import SpanProcessor
from obs_sdk import init_observability

class AuditSpanProcessor(SpanProcessor):
    def on_start(self, span, parent_context):
        print(f"Started span: {span.name}")

provider = init_observability(
    service_name="audited-service",
    span_processors=[AuditSpanProcessor()],
)
```

---

## Testing

Run unit tests with Python's standard `unittest`:

```bash
python -m unittest discover tests
```

