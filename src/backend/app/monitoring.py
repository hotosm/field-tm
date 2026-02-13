# Copyright (c) Humanitarian OpenStreetMap Team
#
# This file is part of Field-TM.
#
#     Field-TM is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     Field-TM is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with Field-TM.  If not, see <https:#www.gnu.org/licenses/>.
#
"""Module to configure different monitoring configs."""

import html
import logging
from typing import Any

from litestar import Litestar, Request, Response
from litestar import status_codes as status
from litestar.exceptions import HTTPException
from litestar.types import ASGIApp, Receive, Scope, Send

log = logging.getLogger(__name__)


def add_endpoint_profiler(app: Litestar) -> None:
    """Add a simple per-request profiler middleware when DEBUG is enabled.

    Wraps the request in a PyInstrument profiler and returns the profiler
    HTML instead of the normal response.
    """
    from urllib.parse import parse_qs

    from pyinstrument import Profiler

    def profiler_middleware(next_app: ASGIApp) -> ASGIApp:
        async def middleware(scope: Scope, receive: Receive, send: Send) -> None:
            # Only act on HTTP requests
            if scope["type"] != "http":
                await next_app(scope, receive, send)
                return

            # Parse query string manually from ASGI scope
            raw_qs = scope.get("query_string", b"").decode()
            params = parse_qs(raw_qs)
            raw_profile = (params.get("profile") or [""])[0].lower()
            profiling = raw_profile in ("1", "true", "yes")

            if not profiling:
                await next_app(scope, receive, send)
                return

            profiler = Profiler(interval=0.001, async_mode="enabled")
            profiler.start()

            status_code = 200

            async def send_wrapper(message: dict[str, Any]) -> None:
                nonlocal status_code
                # Capture original status code but drop the original body –
                # we'll return the profiler HTML instead.
                if message["type"] == "http.response.start":
                    status_code = message.get("status", status_code)
                # We intentionally do not forward the original response to `send`.

            # Run the downstream app once just to exercise the code path
            await next_app(scope, receive, send_wrapper)
            profiler.stop()

            html = profiler.output_html()

            # Return profiler HTML as the final response
            await send(
                {
                    "type": "http.response.start",
                    "status": status_code,
                    "headers": [
                        (b"content-type", b"text/html; charset=utf-8"),
                    ],
                }
            )
            await send(
                {
                    "type": "http.response.body",
                    "body": html.encode("utf-8"),
                    "more_body": False,
                }
            )

        return middleware

    # Register middleware with the Litestar app
    app.middleware.append(profiler_middleware)


def set_sentry_otel_tracer(dsn: str):
    """Add OpenTelemetry tracing only if environment variables configured."""
    from opentelemetry import trace
    from opentelemetry.propagate import set_global_textmap
    from opentelemetry.sdk.trace import TracerProvider
    from sentry_sdk import init
    from sentry_sdk.integrations.opentelemetry import (
        SentryPropagator,
        SentrySpanProcessor,
    )

    init(
        dsn=dsn,
        enable_tracing=True,
        traces_sample_rate=1.0,
        instrumenter="otel",
    )

    provider = TracerProvider()
    provider.add_span_processor(SentrySpanProcessor())
    trace.set_tracer_provider(provider)
    set_global_textmap(SentryPropagator())


def set_otel_tracer(app: Litestar, endpoint: str):
    """Add OpenTelemetry tracing only if environment variables configured."""
    from opentelemetry import trace
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

    # from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import (
        BatchSpanProcessor,
    )

    log.info(f"Adding OpenTelemetry tracing for url: {endpoint}")

    trace.set_tracer_provider(
        TracerProvider(
            resource=Resource.create({}),
        ),
    )

    # from opentelemetry.context import (
    #     Context,
    # )
    # from opentelemetry.sdk.trace import Span
    # class CustomBatchSpanProcessor(BatchSpanProcessor):
    #     def on_start(self, span: Span, parent_context: Optional[Context] = None):
    #         """Startup for Span, override to reduce verbosity of attributes."""
    #         span.set_attributes({
    #             "http.host": "",
    #             "net.host.port": "",
    #             "http.flavor": "",
    #             "http.url": "",
    #             "http.server_name": "",
    #         })

    # Console log processor (for debugging)
    # SimpleSpanProcessor(ConsoleSpanExporter()),
    span_processor = BatchSpanProcessor(
        OTLPSpanExporter(
            endpoint=endpoint,
        )
    )
    trace.get_tracer_provider().add_span_processor(
        span_processor,
    )

    # Ensure the HTTPException text is included in attributes
    async def http_exception_handler(request: Request, exc: HTTPException) -> Response:
        current_span = trace.get_current_span()
        current_span.set_attributes(
            {
                # "span_status": "ERROR",
                "http.status_text": str(exc.detail),
                # "otel.status_description": f"{exc.status_code} / {str(exc.detail)}",
                # "otel.status_code": "ERROR"
            }
        )
        current_span.record_exception(exc)

        # Check if this is an HTMX request - if so, return 200 OK to prevent bunkerweb interception
        is_htmx = request.headers.get("HX-Request") == "true"
        if is_htmx:
            # For HTMX requests, return 200 OK with error component to prevent bunkerweb interception
            escaped_msg = html.escape(
                str(exc.detail) if exc.detail else "An unexpected error occurred"
            )
            error_html = (
                f'<wa-callout variant="danger"><span>{escaped_msg}</span></wa-callout>'
            )
            return Response(
                content=error_html,
                media_type="text/html",
                status_code=status.HTTP_200_OK,
            )

        # For non-HTMX requests, return standard error response
        return Response(
            content={"detail": str(exc.detail)},
            status_code=exc.status_code,
        )

    # Register handler with Litestar
    app.exception_handlers[HTTPException] = http_exception_handler


def set_otel_logger(endpoint: str):
    """Add OpenTelemetry logging only if environment variables configured."""
    from opentelemetry._logs import set_logger_provider
    from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
    from opentelemetry.instrumentation.logging import LoggingInstrumentor
    from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
    from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
    from opentelemetry.sdk.resources import Resource

    log.info(f"Adding OpenTelemetry logging for url: {endpoint}")

    class FormattedLoggingHandler(LoggingHandler):
        def emit(self, record: logging.LogRecord) -> None:
            msg = self.format(record)
            record.msg = msg
            record.args = None
            self._log.emit(self._translate(record))

    logger_provider = LoggerProvider(resource=Resource.create({}))
    set_logger_provider(logger_provider)
    otlp_log_exporter = OTLPLogExporter()
    logger_provider.add_log_record_processor(BatchLogRecordProcessor(otlp_log_exporter))

    otel_log_handler = FormattedLoggingHandler(logger_provider=logger_provider)

    # This has to be called first before log.getLogger().addHandler()
    # so that it can call logging.basicConfig first to set the logging format
    # based on the environment variable OTEL_PYTHON_LOG_FORMAT
    LoggingInstrumentor().instrument()
    log_formatter = logging.Formatter(
        "%(asctime)s.%(msecs)03d [%(levelname)s] %(name)s | "
        "%(funcName)s:%(lineno)d | %(message)s",
        None,
    )
    otel_log_handler.setFormatter(log_formatter)
    logging.getLogger().addHandler(otel_log_handler)


def instrument_app_otel(app: Litestar):
    """Add OpenTelemetry LiteStar instrumentation.

    Only used if environment variables configured.
    """
    from litestar.contrib.opentelemetry import OpenTelemetryConfig, OpenTelemetryPlugin

    open_telemetry_config = OpenTelemetryConfig()
    app.plugins.append(OpenTelemetryPlugin(open_telemetry_config))
