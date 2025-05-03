from dotenv import find_dotenv, load_dotenv
from openai import OpenAI

from obiguard_trace_python_sdk import langtrace
from obiguard_trace_python_sdk.utils.with_root_span import with_langtrace_root_span

_ = load_dotenv(find_dotenv())

langtrace.init(write_spans_to_console=True)


client = OpenAI()


@with_langtrace_root_span()
def images_generate():
    result = client.images.generate(
        model="dall-e-3",
        prompt="A cute baby sea otter",
    )
    print(result)
