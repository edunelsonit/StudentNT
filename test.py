from openai import OpenAI

client = OpenAI(
  base_url="https://api.featherless.ai/v1",
  api_key="rc_9ae58b1be7ff69aa15cc7e2a320424c766b82aeffb9e5967fcf6d3d61add0ded",
)

response = client.chat.completions.create(
  model='Qwen/Qwen2.5-7B-Instruct',
  messages=[
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Hello!"}
  ],
)
print(response.model_dump()['choices'][0]['message']['content'])
