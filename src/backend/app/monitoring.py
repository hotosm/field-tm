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

import logging

from fastapi import FastAPI
from fastapi.exceptions import HTTPException
from fastapi.requests import Request
from fastapi.responses import HTMLResponse, JSONResponse
from loguru import logger as log


def add_endpoint_profiler(app: FastAPI):
    """Add endpoint profiler if DEBUG is enabled."""
    from pyinstrument import Profiler

    @app.middleware("http")
    async def _profile_request(request: Request, call_next):  # dead: disable
        """Calculate the execution time for routes."""
        profiling = request.query_params.get("profile", False)
        if profiling:
            profiler = Profiler(interval=0.001, async_mode="enabled")
            profiler.start()
            await call_next(request)
            profiler.stop()
            return HTMLResponse(profiler.output_html())
        else:
            return await call_next(request)


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


def set_otel_tracer(app: FastAPI, endpoint: str):
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
    @app.exception_handler(HTTPException)
    async def http_exception_handler(
        request,  # dead: disable
        exc,
    ):  # dead: disable
        current_span = trace.get_current_span()
        current_span.set_attributes(
            {
                # "span_status": "ERROR",
                "http.status_text": str(exc.detail),
                # "otel.status_description": f"{exc.status_code} / {str(exc.detail)}",
                # "otel.status_code": "ERROR"
            }
        )
        # current_span.add_event("Test")
        current_span.record_exception(exc)
        return JSONResponse(
            status_code=exc.status_code, content={"detail": str(exc.detail)}
        )


def set_otel_logger(endpoint: str):
    """Add OpenTelemetry logging only if environment variables configured.

    FIXME not quite functional yet.
    FIXME requires better interop with loguru.
    FIXME https://github.com/Delgan/loguru/issues/674
    FIXME https://github.com/open-telemetry/opentelemetry-python/issues/3615
    FIXME Details: https://opentelemetry-python-contrib.readthedocs.io
                    /en/latest/instrumentation/logging/logging.html
    """
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
            self._logger.emit(self._translate(record))

    logger_provider = LoggerProvider(resource=Resource.create({}))
    set_logger_provider(logger_provider)
    otlp_log_exporter = OTLPLogExporter()
    logger_provider.add_log_record_processor(BatchLogRecordProcessor(otlp_log_exporter))

    otel_log_handler = FormattedLoggingHandler(logger_provider=logger_provider)

    # This has to be called first before logger.getLogger().addHandler()
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


def instrument_app_otel(app: FastAPI):
    """Add OpenTelemetry FastAPI instrumentation.

    Only used if environment variables configured.
    """
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.instrumentation.psycopg import PsycopgInstrumentor
    from opentelemetry.instrumentation.requests import RequestsInstrumentor

    FastAPIInstrumentor.instrument_app(app)
    # FastAPIInstrumentor.instrument_app(
    #   app, tracer_provider=trace.get_tracer_provider()
    # )
    PsycopgInstrumentor().instrument(enable_commenter=True, commenter_options={})
    RequestsInstrumentor().instrument()
    # RequestsInstrumentor().instrument(tracer_provider=tracer_provider)
