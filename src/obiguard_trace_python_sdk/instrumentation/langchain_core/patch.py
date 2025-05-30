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

import json

from langtrace.trace_attributes import FrameworkSpanAttributes
from obiguard_trace_python_sdk.utils.llm import get_span_name
from opentelemetry import baggage, trace
from opentelemetry.trace import SpanKind, StatusCode
from opentelemetry.trace.status import Status
from opentelemetry.trace.propagation import set_span_in_context

from obiguard_trace_python_sdk.constants.instrumentation.common import (
    LANGTRACE_ADDITIONAL_SPAN_ATTRIBUTES_KEY,
    SERVICE_PROVIDERS,
)
from importlib_metadata import version as v

from obiguard_trace_python_sdk.constants import LANGTRACE_SDK_NAME
from langtrace.trace_attributes import SpanAttributes


def generic_patch(
    method_name, task, tracer, version, trace_output=True, trace_input=True
):
    """
    Wrapper function to trace a generic method.
    method_name: The name of the method to trace.
    task: The name used to identify the type of task in `generic_patch`.
    tracer: The tracer object used in `generic_patch`.
    version: The version parameter used in `generic_patch`.
    trace_output: Whether to trace the output of the patched methods.
    trace_input: Whether to trace the input of the patched methods.
    """

    def traced_method(wrapped, instance, args, kwargs):
        service_provider = SERVICE_PROVIDERS["LANGCHAIN_CORE"]
        extra_attributes = baggage.get_baggage(LANGTRACE_ADDITIONAL_SPAN_ATTRIBUTES_KEY)

        span_attributes = {
            "langtrace.sdk.name": "obiguard-trace-python-sdk",
            "langtrace.service.name": service_provider,
            "langtrace.service.type": "framework",
            "langtrace.service.version": version,
            "langtrace.version": v(LANGTRACE_SDK_NAME),
            "langchain.task.name": task,
            "gen_ai.request.model": (
                instance.model if hasattr(instance, "model") else None
            ),
            SpanAttributes.LLM_REQUEST_MAX_TOKENS: (
                instance.max_output_tokens
                if hasattr(instance, "max_output_tokens")
                else None
            ),
            SpanAttributes.LLM_TOP_K: (
                instance.top_k if hasattr(instance, "top_k") else None
            ),
            SpanAttributes.LLM_REQUEST_TOP_P: (
                instance.top_p if hasattr(instance, "top_p") else None
            ),
            SpanAttributes.LLM_REQUEST_TEMPERATURE: (
                instance.temperature if hasattr(instance, "temperature") else None
            ),
            **(extra_attributes if extra_attributes is not None else {}),  # type: ignore
        }

        if trace_input and len(args) > 0:
            span_attributes["langchain.inputs"] = to_json_string(args)

        span_attributes["langchain.metadata"] = to_json_string(kwargs)

        attributes = FrameworkSpanAttributes(**span_attributes)

        with tracer.start_as_current_span(
            name=get_span_name(method_name),
            kind=SpanKind.CLIENT,
            context=set_span_in_context(trace.get_current_span()),
        ) as span:

            for field, value in attributes.model_dump(by_alias=True).items():
                if value is not None:
                    span.set_attribute(field, value)
            try:
                # Attempt to call the original method
                result = wrapped(*args, **kwargs)
                if trace_output:
                    span.set_attribute("langchain.outputs", to_json_string(result))
                    if hasattr(result, "usage_metadata") and result.usage_metadata is not None:
                        span.set_attribute(
                            SpanAttributes.LLM_USAGE_PROMPT_TOKENS,
                            result.usage_metadata["input_tokens"],
                        )
                        span.set_attribute(
                            SpanAttributes.LLM_USAGE_COMPLETION_TOKENS,
                            result.usage_metadata["output_tokens"],
                        )
                span.set_status(StatusCode.OK)
                return result
            except Exception as err:
                # Record the exception in the span
                span.record_exception(err)

                # Set the span status to indicate an error
                span.set_status(Status(StatusCode.ERROR, str(err)))

                # Reraise the exception to ensure it's not swallowed
                raise

    return traced_method


def runnable_patch(
    method_name, task, tracer, version, trace_output=True, trace_input=True
):
    """
    Wrapper function to trace a runnable
    method_name: The name of the method to trace.
    task: The name used to identify the type of task in `generic_patch`.
    tracer: The tracer object used in `generic_patch`.
    version: The version parameter used in `generic_patch`.
    trace_output: Whether to trace the output of the patched methods.
    trace_input: Whether to trace the input of the patched methods.
    """

    def traced_method(wrapped, instance, args, kwargs):
        service_provider = SERVICE_PROVIDERS["LANGCHAIN_CORE"]
        span_attributes = {
            "langtrace.sdk.name": "obiguard-trace-python-sdk",
            "langtrace.service.name": service_provider,
            "langtrace.service.type": "framework",
            "langtrace.service.version": version,
            "langtrace.version": v(LANGTRACE_SDK_NAME),
            "langchain.task.name": task,
        }

        if trace_input:
            inputs = {}
            if len(args) > 0:
                for arg in args:
                    if isinstance(arg, dict):
                        for key, value in arg.items():
                            if isinstance(value, list):
                                for item in value:
                                    inputs[key] = item.__class__.__name__
                            elif isinstance(value, str):
                                inputs[key] = value
                    elif isinstance(arg, str):
                        inputs["input"] = arg

            for field, value in (
                instance.steps.items()
                if hasattr(instance, "steps") and isinstance(instance.steps, dict)
                else {}
            ):
                inputs[field] = value.__class__.__name__

            span_attributes["langchain.inputs"] = to_json_string(inputs)

        attributes = FrameworkSpanAttributes(**span_attributes)

        with tracer.start_as_current_span(
            method_name,
            kind=SpanKind.CLIENT,
            context=set_span_in_context(trace.get_current_span()),
        ) as span:
            for field, value in attributes.model_dump(by_alias=True).items():
                if value is not None:
                    span.set_attribute(field, value)
            try:
                # Attempt to call the original method
                result = wrapped(*args, **kwargs)

                if trace_output:
                    outputs = {}
                    if isinstance(result, dict):
                        for field, value in (
                            result.items() if hasattr(result, "items") else {}
                        ):
                            if isinstance(value, list):
                                for item in value:
                                    if item.__class__.__name__ == "Document":
                                        outputs[field] = "Document"
                                    else:
                                        outputs[field] = item.__class__.__name__
                            if isinstance(value, str):
                                outputs[field] = value
                    span.set_attribute("langchain.outputs", to_json_string(outputs))
                    if isinstance(result, str):
                        span.set_attribute("langchain.outputs", result)

                span.set_status(StatusCode.OK)
                return result
            except Exception as err:
                # Record the exception in the span
                span.record_exception(err)

                # Set the span status to indicate an error
                span.set_status(Status(StatusCode.ERROR, str(err)))

                # Reraise the exception to ensure it's not swallowed
                raise

    return traced_method


def clean_empty(d):
    """Recursively remove empty lists, empty dicts, or None elements from a dictionary."""
    if not isinstance(d, (dict, list, tuple)):
        return d
    if isinstance(d, tuple):
        return tuple(
            val
            for val in (clean_empty(val) for val in d)
            if val != () and val is not None
        )
    if isinstance(d, list):
        return [
            val
            for val in (clean_empty(val) for val in d)
            if val != [] and val is not None
        ]
    result = {}
    for k, val in d.items():
        if isinstance(val, dict):
            val = clean_empty(val)
            if val != {} and val is not None:
                result[k] = val
        elif isinstance(val, list):
            val = [clean_empty(value) for value in val]
            if val != [] and val is not None:
                result[k] = val
        elif isinstance(val, str) and val is not None:
            if val.strip() != "":
                result[k] = val.strip()
        elif isinstance(val, object):
            # some langchain objects have a text attribute
            val = getattr(val, "text", None)
            if val is not None and isinstance(val, str):
                if val.strip() != "":
                    result[k] = val.strip()
    return result


def custom_serializer(obj):
    """Fallback function to convert unserializable objects."""
    if hasattr(obj, "__dict__"):
        # Attempt to serialize custom objects by their __dict__ attribute.
        return clean_empty(obj.__dict__)
    else:
        # For other types, just convert to string
        return str(obj)


def to_json_string(any_object):
    """Converts any object to a JSON-parseable string, omitting empty or None values."""
    try:
        cleaned_object = clean_empty(any_object)
        return json.dumps(cleaned_object, default=custom_serializer, indent=2)
    except NotImplementedError:
        # Handle specific types that raise this error
        return str(any_object)  # or another appropriate fallback
    except TypeError:
        # Handle cases where obj is not serializable
        return str(any_object)
