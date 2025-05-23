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
import logging
from typing import Collection

from opentelemetry.instrumentation.instrumentor import BaseInstrumentor
from opentelemetry.trace import get_tracer
from wrapt import wrap_function_wrapper

from obiguard_trace_python_sdk.constants.instrumentation.pinecone import APIS
from obiguard_trace_python_sdk.instrumentation.pinecone.patch import generic_patch

logging.basicConfig(level=logging.FATAL)


class PineconeInstrumentation(BaseInstrumentor):
    """
    The PineconeInstrumentation class represents the Pinecone instrumentation"""

    def instrumentation_dependencies(self) -> Collection[str]:
        return ["pinecone >= 3.1.0"]

    def _instrument(self, **kwargs):
        tracer_provider = kwargs.get("tracer_provider")
        tracer = get_tracer(__name__, "", tracer_provider)
        version = importlib.metadata.version("pinecone")
        for operation_name, details in APIS.items():
            operation = details["OPERATION"]
            # Dynamically creating the patching call
            wrap_function_wrapper(
                "pinecone.data.index",
                f"Index.{operation}",
                generic_patch(operation_name, version, tracer),
            )

    def _uninstrument(self, **kwargs):
        pass
