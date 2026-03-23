from openai import OpenAI
from config import settings

client = OpenAI(
    base_url=settings.OPENAI_BASE_URL,
    api_key=settings.OPENAI_API_KEY,
)


def generate_learning(topic,country):
    prompt = f"""
    Teach {country} students about {topic}.

    Include:
    - Lesson
    - Examples using local foods
    - 3 quiz questions
    """

    response = client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        max_tokens=4096,
        messages=[
            {"role": "system", "content": "You are an Experience nutrition teacher."},
            {"role": "user", "content": prompt}
        ],
    )

    return response.choices[0].message.content


"""from openai import OpenAI
import os

client = OpenAI(
  base_url="https://api.featherless.ai/v1",
  api_key="rc_9ae58b1be7ff69aa15cc7e2a320424c766b82aeffb9e5967fcf6d3d61add0ded",
)

response = client.chat.completions.create(
  model='Qwen/Qwen2.5-7B-Instruct',
  max_tokens=4096,
  messages=[
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Hello!"}
  ],
)
print(response.model_dump()['choices'][0]['message']['content'])
"""