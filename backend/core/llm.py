import os
import time
import random
from abc import ABC, abstractmethod
from dotenv import load_dotenv

load_dotenv()

class BaseLLM(ABC):
    @abstractmethod
    def generate_content(self, prompt: str) -> str:
        pass

    @abstractmethod
    def get_embedding(self, text: str, task_type: str = "retrieval_document") -> list[float]:
        pass

class GoogleLLM(BaseLLM):
    def __init__(self):
        import google.generativeai as genai
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable not set")
        
        genai.configure(api_key=api_key)
        self.model_name = os.getenv("GEMINI_MODEL_NAME", "gemini-1.5-flash")
        self.model = genai.GenerativeModel(self.model_name)
        self.embedding_model = 'models/gemini-embedding-001'

    def _retry_on_429(self, func, *args, **kwargs):
        max_retries = 3
        delay = 2
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                err_str = str(e).lower()
                if "429" in err_str or "resource_exhausted" in err_str:
                    if attempt < max_retries - 1:
                        wait = delay * (2 ** attempt) + random.uniform(0, 1)
                        print(f"Quota reached (429). Retrying in {wait:.2f}s... (Attempt {attempt+1})")
                        time.sleep(wait)
                        continue
                raise e

    def generate_content(self, prompt: str) -> str:
        try:
            response = self._retry_on_429(self.model.generate_content, prompt)
            if not response or not response.text:
                return "I'm sorry, I couldn't generate a response."
            return response.text
        except Exception as e:
            print(f"LLM Generation Error: {e}")
            return f"Error: {str(e)}"

    def get_embedding(self, text: str, task_type: str = "retrieval_document") -> list[float]:
        import google.generativeai as genai
        try:
            result = self._retry_on_429(
                genai.embed_content,
                model=self.embedding_model,
                content=text,
                task_type=task_type
            )
            return result['embedding']
        except Exception as e:
            print(f"Embedding Error: {e}")
            return [0.0] * 768

class OpenAILLM(BaseLLM):
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model_name = os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini")
        self.embedding_model = "text-embedding-3-small"
        self._client = None

    @property
    def client(self):
        if self._client is None:
            if not self.api_key or self.api_key == "your_openai_api_key_here":
                raise ValueError("OPENAI_API_KEY environment variable not set correctly. Please update your .env file.")
            from openai import OpenAI
            self._client = OpenAI(api_key=self.api_key)
        return self._client

    def generate_content(self, prompt: str) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"OpenAI Generation Error: {e}")
            return f"Error: {str(e)}"

    def get_embedding(self, text: str, task_type: str = "retrieval_document") -> list[float]:
        try:
            # text-embedding-3-small is 1536 dims
            response = self.client.embeddings.create(
                input=[text],
                model=self.embedding_model
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"OpenAI Embedding Error: {e}")
            return [0.0] * 1536

def get_llm() -> BaseLLM:
    provider = os.getenv("MODEL_PROVIDER", "google").lower()
    if provider == "openai":
        return OpenAILLM()
    return GoogleLLM()
