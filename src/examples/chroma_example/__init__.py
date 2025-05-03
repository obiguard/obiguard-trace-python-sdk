from examples.chroma_example.basic import basic
from obiguard_trace_python_sdk import with_langtrace_root_span


class ChromaRunner:
    @with_langtrace_root_span("Chroma")
    def run(self):
        basic()
