from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, BatchSpanProcessor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.dbapi import trace_integration
from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor
import redis
from minio import Minio
from minio.error import S3Error
from clickhouse_driver import Client
import psycopg2
import os
import tempfile

# --- Setup OpenTelemetry ---
trace.set_tracer_provider(TracerProvider())
console_exporter = ConsoleSpanExporter()
trace.get_tracer_provider().add_span_processor(BatchSpanProcessor(console_exporter))

# Auto-instrument all libraries
RedisInstrumentor().instrument()
RequestsInstrumentor().instrument()
trace_integration(enable=True)
Psycopg2Instrumentor().instrument()

# --- Create a parent span for the entire workflow ---
tracer = trace.get_tracer(__name__)
with tracer.start_as_current_span("multi_db_workflow") as parent_span:
    # --- 1. Valkey (Redis) ---
    try:
        r = redis.Redis(host="localhost", port=6379, db=0)
        with tracer.start_as_current_span("valkey_operation"):
            r.set("test_key", "test_value")
            print("Valkey: SET test_key")
    except Exception as e:
        print(f"Valkey error: {e}")

    # --- 2. MinIO ---
    try:
        # Create a temp file for MinIO upload
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"test data")
            tmp_path = tmp.name

        client = Minio(
            "play.min.io",
            access_key="Q3AM3UQ867SPQQA43P2F",
            secret_key="zuf+tfteSlswRu7BJ86wekitnifILbZam1KYY3TG",
            secure=True,
        )
        with tracer.start_as_current_span("minio_operation"):
            client.fput_object("test-bucket", "test-object", tmp_path)
            print("MinIO: Uploaded test-object")
        os.unlink(tmp_path)
    except S3Error as e:
        print(f"MinIO error: {e}")

    # --- 3. ClickHouse ---
    try:
        ch_client = Client(host="localhost")
        with tracer.start_as_current_span("clickhouse_operation"):
            result = ch_client.execute("SELECT 1")
            print(f"ClickHouse: {result}")
    except Exception as e:
        print(f"ClickHouse error: {e}")

    # --- 4. PostgreSQL ---
    try:
        conn = psycopg2.connect("dbname=test user=postgres password=postgres host=localhost")
        cur = conn.cursor()
        with tracer.start_as_current_span("postgres_operation"):
            cur.execute("SELECT 1")
            result = cur.fetchone()
            print(f"PostgreSQL: {result}")
        conn.close()
    except Exception as e:
        print(f"PostgreSQL error: {e}")

print("\n--- Trace exported to console above ---")