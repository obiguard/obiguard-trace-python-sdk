import asyncio
from examples.graphlit_example.conversation import complete
from obiguard_trace_python_sdk import with_langtrace_root_span


class GraphlitRunner:
    @with_langtrace_root_span("GraphlitRun")
    def run(self):
        asyncio.run(complete())
