from openai import OpenAI
from config import settings

client = OpenAI(
    base_url=settings.OPENAI_BASE_URL,
    api_key=settings.OPENAI_API_KEY,
)

def generate_learning_stream(country, topic):
    prompt = f"""
    Teach {country} students about {topic}.
    Structure:
    1. Detailed lesson with local food examples from {country}.
    2. A section labeled 'QUIZ_SECTION'.
    3. Exactly 3 questions in this format:
    Q: [Question]
    A) [Option]
    B) [Option]
    C) [Option]
    D) [Option]
    Answer: [Letter]
    """

    stream = client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=[
            {"role": "system", "content": "You are a professional nutrition educator."},
            {"role": "user", "content": prompt}
        ],
        stream=True
    )
    
    for chunk in stream:
        if hasattr(chunk, 'choices') and len(chunk.choices) > 0:
            content = chunk.choices[0].delta.content
            if content:
                yield content