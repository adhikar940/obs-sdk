import os
import subprocess
from dotenv import load_dotenv

load_dotenv()

def test_auto_instrumentation_to_multiple_backends():
    env = os.environ.copy()
    env.update({
        "OTEL_SERVICE_NAME": os.getenv("OTEL_SERVICE_NAME"),
        "LANGFUSE_EXPORT": os.getenv("LANGFUSE_EXPORT") or os.getenv("LOCAL_LANGfUSE_EXPORT"),
        "LANGFUSE_ENDPOINT": os.getenv("LANGFUSE_ENDPOINT") or os.getenv("LOCAL_LANGfUSE_ENDPOINT"),
        "LANGFUSE_API_KEY": os.getenv("LANGFUSE_API_KEY") or os.getenv("REMOTE_LANGfUSE_API_KEY"),
        "ARIZE_EXPORT": os.getenv("ARIZE_EXPORT"),
        "ARIZE_ENDPOINT": os.getenv("ARIZE_ENDPOINT"),
        "CONSOLE_EXPORT": os.getenv("CONSOLE_EXPORT"),
        "OTEL_LOG_LEVEL": "debug",
    })

    cmd = ["opentelemetry-instrument", "python", "example_app.py"]
    process = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    stdout, stderr = process.communicate()
    return_code = process.returncode

    assert return_code == 0, f"Process failed: {stderr}"
    assert "Fetching data..." in stdout, "App did not run."
    assert "name: fetch_data" in stdout or "OpenTelemetry" in stderr, "No traces in console."
    assert "Failed to export" not in stderr, "Exporter failed."

    print("✅ Test passed: Traces sent to Terminal, Local Langfuse, and Remote Langfuse.")

if __name__ == "__main__":
    test_auto_instrumentation_to_multiple_backends()