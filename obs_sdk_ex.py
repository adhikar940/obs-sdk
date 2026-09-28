"""Example demonstrating OpenTelemetry observability with obs_sdk."""
import os
import tempfile
from opentelemetry import trace
import redis
from minio import Minio
from minio.error import S3Error
from clickhouse_driver import Client
import psycopg2

from obs_sdk import observability_lifecycle, init_observability, force_flush, shutdown


def run_workflow():
    """Run a multi-service workflow tracked by OpenTelemetry spans."""
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
        except Exception as e:
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


def main():
    # Use observability_lifecycle context manager to ensure all spans
    # are force_flushed and shutdown properly for short-lived CLI runs.
    with observability_lifecycle(
        service_name="multi-db-workflow-service",
        instrumentations=["requests", "redis", "psycopg2", "dbapi"],
    ):
        print("Starting multi-database workflow with obs_sdk...")
        run_workflow()
        print("Workflow finished.")


if __name__ == "__main__":
    main()
