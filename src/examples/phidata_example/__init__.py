import asyncio
from examples.phidata_example.agent import agent_run
from obiguard_trace_python_sdk import langtrace

langtrace.init()

class PhiDataRunner:
    def run(self):
        agent_run()
