"""
Copyright (c) 2024 Scale3 Labs

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import importlib.metadata
import inspect
from typing import Collection

from opentelemetry.instrumentation.instrumentor import BaseInstrumentor
from opentelemetry.trace import get_tracer
from wrapt import wrap_function_wrapper

from obiguard_trace_python_sdk.instrumentation.langgraph.patch import patch_graph_methods


class LanggraphInstrumentation(BaseInstrumentor):
    """
    Instrumentor for langgraph.
    """

    def instrumentation_dependencies(self) -> Collection[str]:
        return ["langgraph >= 0.0.39"]

    def _instrument(self, **kwargs):
        tracer_provider = kwargs.get("tracer_provider")
        tracer = get_tracer(__name__, "", tracer_provider)
        version = importlib.metadata.version("langgraph")

        # List of modules to patch, with their corresponding patch names
        modules_to_patch = [
            (
                "langgraph.graph.state",  # Updated module path
                "StateGraph",  # Updated class name
                [
                    "add_node",
                    "add_edge",
                    "set_entry_point",
                    "set_finish_point",
                    "add_conditional_edges",
                ],
            )
        ]

        for module_name, class_name, methods in modules_to_patch:
            for method_name in methods:
                # Construct the correct path for the method
                method_path = f"{class_name}.{method_name}"
                wrap_function_wrapper(
                    module_name,
                    method_path,
                    patch_graph_methods(
                        f"{module_name}.{method_path}", tracer, version
                    ),
                )

    def _uninstrument(self, **kwargs):
        pass
