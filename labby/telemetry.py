from opentelemetry import trace
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.richconsole import RichConsoleSpanExporter
from opentelemetry.sdk.trace import TracerProvider

trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer(__name__)
 
tracer.add_span_processor(BatchSpanProcessor(RichConsoleSpanExporter()))  # type: ignore