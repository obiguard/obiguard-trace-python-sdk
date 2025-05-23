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
from typing import Collection

from opentelemetry.instrumentation.instrumentor import BaseInstrumentor
from opentelemetry.trace import get_tracer
from wrapt import wrap_function_wrapper

from obiguard_trace_python_sdk.instrumentation.cohere.patch import (
    chat_create,
    chat_create_v2,
    chat_stream,
    embed,
    rerank,
)


class CohereInstrumentation(BaseInstrumentor):
    """
    The CohereInstrumentation class represents the Anthropic instrumentation
    """

    def instrumentation_dependencies(self) -> Collection[str]:
        return ["cohere >= 5.0.0"]

    def _instrument(self, **kwargs):
        tracer_provider = kwargs.get("tracer_provider")
        tracer = get_tracer(__name__, "", tracer_provider)
        version = importlib.metadata.version("cohere")

        wrap_function_wrapper(
            "cohere.client",
            "Client.chat",
            chat_create("cohere.client.chat", version, tracer),
        )

        wrap_function_wrapper(
            "cohere.client_v2",
            "ClientV2.chat",
            chat_create_v2("cohere.client_v2.chat", version, tracer),
        )

        wrap_function_wrapper(
            "cohere.client_v2",
            "ClientV2.chat_stream",
            chat_create_v2("cohere.client_v2.chat", version, tracer, stream=True),
        )

        wrap_function_wrapper(
            "cohere.client",
            "Client.chat_stream",
            chat_stream("cohere.client.chat_stream", version, tracer),
        )

        wrap_function_wrapper(
            "cohere.client",
            "Client.embed",
            embed("cohere.client.embed", version, tracer),
        )

        wrap_function_wrapper(
            "cohere.client_v2",
            "ClientV2.embed",
            embed("cohere.client.embed", version, tracer, v2=True),
        )

        wrap_function_wrapper(
            "cohere.client",
            "Client.rerank",
            rerank("cohere.client.rerank", version, tracer),
        )

        wrap_function_wrapper(
            "cohere.client_v2",
            "ClientV2.rerank",
            rerank("cohere.client.rerank", version, tracer, v2=True),
        )

    def _instrument_module(self, module_name):
        pass

    def _uninstrument(self, **kwargs):
        pass
