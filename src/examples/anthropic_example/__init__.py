from examples.anthropic_example.completion import messages_create
from obiguard_trace_python_sdk import with_langtrace_root_span


class AnthropicRunner:
    @with_langtrace_root_span("Anthropic")
    def run(self):
        messages_create()
