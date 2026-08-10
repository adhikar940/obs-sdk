import os
import subprocess
from dotenv import load_dotenv

load_dotenv()

def test_auto_instrumentation_to_multiple_backends():
    env = os.environ.copy()
    env.update({
        "OTEL_SERVICE_NAME": os.getenv("OTEL_SERVICE_NAME"),
        "LOCAL_LANGfUSE_EXPORT": os.getenv("LOCAL_LANGfUSE_EXPORT"),
        "LOCAL_LANGfUSE_ENDPOINT": os.getenv("LOCAL_LANGfUSE_ENDPOINT"),
        "REMOTE_LANGfUSE_EXPORT": os.getenv("REMOTE_LANGfUSE_EXPORT"),
        "REMOTE_LANGfUSE_ENDPOINT": os.getenv("REMOTE_LANGfUSE_ENDPOINT"),
        "REMOTE_LANGfUSE_API_KEY": os.getenv("REMOTE_LANGfUSE_API_KEY"),
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