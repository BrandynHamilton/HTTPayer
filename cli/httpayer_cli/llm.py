# httpayer_cli/llm.py
import os
import openai

class LLMProvider:
    def complete(self, system: str, prompt: str) -> str:
        raise NotImplementedError

class OpenAIProvider(LLMProvider):
    def __init__(self, model="gpt-4o-mini", api_key=None):
        self.model = model
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise RuntimeError("No OpenAI API key set")

    def complete(self, system: str, prompt: str) -> str:
        client = openai.OpenAI(api_key=self.api_key)
        resp = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            temperature=0,
        )
        return resp.choices[0].message.content
