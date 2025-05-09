from .basic import execute_query
from obiguard_trace_python_sdk import with_langtrace_root_span


class Neo4jRunner:
    @with_langtrace_root_span("Neo4jRunner")
    def run(self):
        execute_query()
