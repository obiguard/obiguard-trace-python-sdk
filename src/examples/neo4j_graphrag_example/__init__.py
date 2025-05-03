import asyncio
from .basic import search
from obiguard_trace_python_sdk import with_langtrace_root_span


class Neo4jGraphRagRunner:
    @with_langtrace_root_span("Neo4jGraphRagRunner")
    def run(self):
        asyncio.run(search())
