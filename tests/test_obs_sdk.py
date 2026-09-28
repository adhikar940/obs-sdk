import os
import unittest
from unittest.mock import MagicMock, patch

from opentelemetry.sdk.trace import TracerProvider, SpanProcessor
from opentelemetry.sdk.resources import Resource, SERVICE_NAME

import obs_sdk
from obs_sdk import (
    init_observability,
    force_flush,
    shutdown,
    observability_lifecycle,
    load_config,
    setup_span_processors,
    setup_auto_instrumentation,
)


class TestObsSDK(unittest.TestCase):

    def setUp(self):
        # Reset any active global provider
        obs_sdk._ACTIVE_PROVIDER = None
        from opentelemetry import trace
        if hasattr(trace, "_TRACER_PROVIDER_SET_ONCE"):
            trace._TRACER_PROVIDER_SET_ONCE._done = False
        if hasattr(trace, "_TRACER_PROVIDER"):
            trace._TRACER_PROVIDER = None

    def tearDown(self):
        obs_sdk.shutdown()

    def test_service_name_as_otel_resource_attribute(self):
        """Verify service_name is attached to the OTel Resource attribute."""
        provider = init_observability(service_name="payment-service", auto_instrument=False)
        self.assertIsInstance(provider, TracerProvider)
        self.assertEqual(provider.resource.attributes[SERVICE_NAME], "payment-service")
        self.assertEqual(provider.resource.attributes["service.name"], "payment-service")

    def test_service_name_from_config(self):
        """Verify service_name from config / env is used if not provided explicitly."""
        with patch.dict(os.environ, {"OTEL_SERVICE_NAME": "config-service"}):
            provider = init_observability(auto_instrument=False)
            self.assertEqual(provider.resource.attributes[SERVICE_NAME], "config-service")

    def test_custom_resource_attributes_merged(self):
        """Verify additional resource_attributes are properly merged."""
        provider = init_observability(
            service_name="analytics-service",
            resource_attributes={"deployment.environment": "staging", "version": "1.2.3"},
            auto_instrument=False,
        )
        self.assertEqual(provider.resource.attributes["service.name"], "analytics-service")
        self.assertEqual(provider.resource.attributes["deployment.environment"], "staging")
        self.assertEqual(provider.resource.attributes["version"], "1.2.3")

    def test_no_extra_unconfigured_batch_span_processor(self):
        """Verify no extra BatchSpanProcessor is added when no exporters or custom processors are configured."""
        provider = init_observability(
            service_name="clean-provider-test",
            auto_instrument=False,
            config={
                "langfuse_export": False,
                "arize_export": False,
                "console_export": False,
            },
        )
        active_processors = provider._active_span_processor._span_processors
        self.assertEqual(len(active_processors), 0)

    def test_setup_span_processors_with_custom_processors(self):
        """Verify custom SpanProcessor instances can be added via parameter or config."""
        mock_processor = MagicMock(spec=SpanProcessor)
        provider = init_observability(
            service_name="custom-processor-test",
            span_processors=[mock_processor],
            auto_instrument=False,
            config={
                "langfuse_export": False,
                "arize_export": False,
                "console_export": False,
            },
        )
        active_processors = provider._active_span_processor._span_processors
        self.assertEqual(len(active_processors), 1)
        self.assertIn(mock_processor, active_processors)

    def test_force_flush_and_shutdown_lifecycle(self):
        """Verify force_flush and shutdown lifecycle methods function correctly."""
        provider = init_observability("lifecycle-test", auto_instrument=False)
        self.assertIs(obs_sdk._ACTIVE_PROVIDER, provider)

        # Test force_flush
        flush_result = force_flush(timeout_millis=5000)
        self.assertTrue(flush_result)

        # Test shutdown
        shutdown()
        self.assertIsNone(obs_sdk._ACTIVE_PROVIDER)

        # Repeated shutdown should be safe and idempotent
        shutdown()

    def test_observability_lifecycle_context_manager(self):
        """Verify observability_lifecycle initializes provider and executes flush and shutdown upon exit."""
        with patch("obs_sdk.force_flush") as mock_flush, patch("obs_sdk.shutdown") as mock_shutdown:
            with observability_lifecycle("cli-test-service", auto_instrument=False) as tp:
                self.assertIsInstance(tp, TracerProvider)
                self.assertEqual(tp.resource.attributes["service.name"], "cli-test-service")

            mock_flush.assert_called_once()
            mock_shutdown.assert_called_once()

    def test_observability_lifecycle_flushes_on_exception(self):
        """Verify observability_lifecycle ensures flush and shutdown even if an exception occurs."""
        with patch("obs_sdk.force_flush") as mock_flush, patch("obs_sdk.shutdown") as mock_shutdown:
            with self.assertRaises(RuntimeError):
                with observability_lifecycle("failing-cli", auto_instrument=False):
                    raise RuntimeError("Something failed")

            mock_flush.assert_called_once()
            mock_shutdown.assert_called_once()

    def test_auto_instrumentation_with_configurable_list(self):
        """Verify setup_auto_instrumentation respects configurable lists of targets."""
        mock_inst1 = MagicMock()
        mock_inst2 = MagicMock()

        enabled = setup_auto_instrumentation(instrumentations=[mock_inst1, mock_inst2])
        mock_inst1.instrument.assert_called_once()
        mock_inst2.instrument.assert_called_once()
        self.assertEqual(len(enabled), 2)

    def test_auto_instrumentation_empty_list(self):
        """Verify passing an empty list disables auto-instrumentation."""
        enabled = setup_auto_instrumentation(instrumentations=[])
        self.assertEqual(enabled, [])

    def test_auto_instrumentation_http_clients(self):
        """Verify requests, httpx, urllib, urllib3, urlibb, and aiohttp auto-instrumentors."""
        from obs_sdk.instrumentation import KNOWN_INSTRUMENTORS

        self.assertIn("requests", KNOWN_INSTRUMENTORS)
        self.assertIn("httpx", KNOWN_INSTRUMENTORS)
        self.assertIn("urllib", KNOWN_INSTRUMENTORS)
        self.assertIn("urllib3", KNOWN_INSTRUMENTORS)
        self.assertIn("urlibb", KNOWN_INSTRUMENTORS)
        self.assertIn("aiohttp", KNOWN_INSTRUMENTORS)
        self.assertIn("aiohttp_client", KNOWN_INSTRUMENTORS)

        # Test execution with mocks
        with patch.dict(KNOWN_INSTRUMENTORS, {
            "requests": MagicMock(),
            "httpx": MagicMock(),
            "urllib": MagicMock(),
            "urllib3": MagicMock(),
            "urlibb": MagicMock(),
            "aiohttp": MagicMock(),
        }):
            targets = ["requests", "httpx", "urllib", "urllib3", "urlibb", "aiohttp"]
            enabled = setup_auto_instrumentation(instrumentations=targets)
            self.assertEqual(len(enabled), 6)
            for target in targets:
                KNOWN_INSTRUMENTORS[target].assert_called_once()

    def test_auto_instrumentation_postgres(self):
        """Verify postgres, postgresql, postgress (typo), psycopg, psycopg2, and asyncpg auto-instrumentors."""
        from obs_sdk.instrumentation import KNOWN_INSTRUMENTORS

        self.assertIn("postgres", KNOWN_INSTRUMENTORS)
        self.assertIn("postgresql", KNOWN_INSTRUMENTORS)
        self.assertIn("postgress", KNOWN_INSTRUMENTORS)
        self.assertIn("psycopg2", KNOWN_INSTRUMENTORS)
        self.assertIn("psycopg", KNOWN_INSTRUMENTORS)
        self.assertIn("asyncpg", KNOWN_INSTRUMENTORS)

        with patch.dict(KNOWN_INSTRUMENTORS, {
            "postgres": MagicMock(),
            "postgresql": MagicMock(),
            "postgress": MagicMock(),
            "psycopg2": MagicMock(),
            "psycopg": MagicMock(),
            "asyncpg": MagicMock(),
        }):
            targets = ["postgres", "postgresql", "postgress", "psycopg2", "psycopg", "asyncpg"]
            enabled = setup_auto_instrumentation(instrumentations=targets)
            self.assertEqual(len(enabled), 6)
            for target in targets:
                KNOWN_INSTRUMENTORS[target].assert_called_once()

    def test_init_observability_disables_auto_instrumentation(self):
        """Verify auto_instrument=False skips setup_auto_instrumentation."""
        with patch("obs_sdk.setup_auto_instrumentation") as mock_setup:
            init_observability("no-auto-inst", auto_instrument=False)
            mock_setup.assert_not_called()

    def test_init_observability_passes_configurable_instrumentations(self):
        """Verify init_observability forwards the configured instrumentations list."""
        custom_list = ["requests", "redis"]
        with patch("obs_sdk.setup_auto_instrumentation") as mock_setup:
            init_observability("custom-inst", instrumentations=custom_list)
            mock_setup.assert_called_once_with(instrumentations=custom_list)

    def test_load_config_parsing(self):
        """Verify load_config handles environment variables and defaults correctly."""
        env = {
            "OTEL_SERVICE_NAME": "env-service",
            "OTEL_EXPORTER_OTLP_PROTOCOL": "http",
            "LANGFUSE_EXPORT": "true",
            "LANGFUSE_ENDPOINT": "http://localhost:3000/api/public/otel",
            "LANGFUSE_API_KEY": "test-key",
            "LANGFUSE_PROTOCOL": "http",
            "ARIZE_EXPORT": "true",
            "ARIZE_ENDPOINT": "http://localhost:6006/v1/traces",
            "ARIZE_PROTOCOL": "http",
            "ARIZE_API_KEY": "phoenix-key",
            "ARIZE_PROJECT_NAME": "my-project",
            "AUTO_INSTRUMENT": "true",
            "AUTO_INSTRUMENTATIONS": "requests, redis , psycopg2",
        }
        with patch.dict(os.environ, env, clear=True):
            cfg = load_config()
            self.assertEqual(cfg["service_name"], "env-service")
            self.assertEqual(cfg["protocol"], "http")
            self.assertTrue(cfg["langfuse_export"])
            self.assertEqual(cfg["langfuse_endpoint"], "http://localhost:3000/api/public/otel")
            self.assertEqual(cfg["langfuse_api_key"], "test-key")
            self.assertEqual(cfg["langfuse_protocol"], "http")
            self.assertTrue(cfg["arize_export"])
            self.assertEqual(cfg["arize_endpoint"], "http://localhost:6006/v1/traces")
            self.assertEqual(cfg["arize_protocol"], "http")
            self.assertEqual(cfg["arize_api_key"], "phoenix-key")
            self.assertEqual(cfg["arize_project_name"], "my-project")
            self.assertTrue(cfg["auto_instrument"])
            self.assertEqual(cfg["instrumentations"], ["requests", "redis", "psycopg2"])

    def test_default_protocol_is_http(self):
        """Verify default protocol is HTTP and instantiates HTTP exporter."""
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
            OTLPSpanExporter as HTTPExporter,
        )
        exporter = obs_sdk.create_otlp_exporter("http://localhost:4318")
        self.assertIsInstance(exporter, HTTPExporter)

    def test_switch_protocol_to_grpc(self):
        """Verify switching protocol to gRPC instantiates gRPC exporter."""
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
            OTLPSpanExporter as GRPCExporter,
        )
        exporter = obs_sdk.create_otlp_exporter("localhost:4317", protocol="grpc")
        self.assertIsInstance(exporter, GRPCExporter)

    def test_langfuse_export_http(self):
        """Verify langfuse_export=True configures Langfuse exporter via HTTP."""
        provider = init_observability(
            service_name="langfuse-http-test",
            auto_instrument=False,
            config={
                "langfuse_export": True,
                "langfuse_endpoint": "http://localhost:3000/api/public/otel",
                "langfuse_protocol": "http",
                "arize_export": False,
                "console_export": False,
            },
        )
        processors = provider._active_span_processor._span_processors
        self.assertEqual(len(processors), 1)

    def test_langfuse_export_grpc(self):
        """Verify langfuse_export=True configures Langfuse exporter via gRPC."""
        provider = init_observability(
            service_name="langfuse-grpc-test",
            auto_instrument=False,
            config={
                "langfuse_export": True,
                "langfuse_endpoint": "localhost:4317",
                "langfuse_protocol": "grpc",
                "arize_export": False,
                "console_export": False,
            },
        )
        processors = provider._active_span_processor._span_processors
        self.assertEqual(len(processors), 1)

    def test_arize_phoenix_export_http(self):
        """Verify arize_export=True configures an Arize Phoenix exporter via HTTP."""
        provider = init_observability(
            service_name="arize-http-test",
            auto_instrument=False,
            config={
                "arize_export": True,
                "arize_endpoint": "http://localhost:6006/v1/traces",
                "arize_protocol": "http",
                "langfuse_export": False,
                "console_export": False,
            },
        )
        processors = provider._active_span_processor._span_processors
        self.assertEqual(len(processors), 1)

    def test_arize_phoenix_export_grpc(self):
        """Verify arize_export=True configures an Arize Phoenix exporter via gRPC."""
        provider = init_observability(
            service_name="arize-grpc-test",
            auto_instrument=False,
            config={
                "arize_export": True,
                "arize_endpoint": "localhost:14317",
                "arize_protocol": "grpc",
                "langfuse_export": False,
                "console_export": False,
            },
        )
        processors = provider._active_span_processor._span_processors
        self.assertEqual(len(processors), 1)


if __name__ == "__main__":
    unittest.main()
