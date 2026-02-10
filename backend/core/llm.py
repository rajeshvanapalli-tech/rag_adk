import os
import time
import random
from abc import ABC, abstractmethod
from dotenv import load_dotenv

load_dotenv()

class BaseLLM(ABC):
    @property
    @abstractmethod
    def model_name(self) -> str:
        pass

    @abstractmethod
    def generate_content(self, prompt: str) -> str:
        pass

    @abstractmethod
    def get_embedding(self, text: str, task_type: str = "retrieval_document") -> list[float]:
        pass

class GoogleLLM(BaseLLM):
    def __init__(self):
        import google.generativeai as genai
        self.api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        self._model_name = os.getenv("GEMINI_MODEL") or os.getenv("GEMINI_MODEL_NAME")
        
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY or GOOGLE_API_KEY environment variable not set")
        
        if not self._model_name:
            # Note: We do not hardcode a fallback as per instructions.
            # If the user hasn't provided it, we let the SDK attempt initialization
            # or report it as part of provider initialization failure.
            pass

        try:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(self._model_name) if self._model_name else None
            self.embedding_model = 'models/gemini-embedding-001'
        except Exception as e:
            raise RuntimeError(f"Google Gemini Provider Initialization Failed: {str(e)}")

    @property
    def model_name(self) -> str:
        return self._model_name or "unspecified"

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
        if not self.model:
            return "Error: Gemini model not configured. Please set GEMINI_MODEL in .env."
        try:
            response = self._retry_on_429(self.model.generate_content, prompt)
            if not response or not response.text:
                return "I'm sorry, I couldn't generate a response."
            return response.text
        except Exception as e:
            print(f"LLM Generation Error: {e}")
            return f"Error: Provider failed to generate content. {str(e)}"

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
        self._model_name = os.getenv("OPENAI_MODEL")
        self.embedding_model = "text-embedding-3-small"
        self._client = None
        
        if not self.api_key or self.api_key == "your_openai_api_key_here":
            raise ValueError("OPENAI_API_KEY environment variable not set correctly.")

    @property
    def model_name(self) -> str:
        return self._model_name or "unspecified"

    @property
    def client(self):
        if self._client is None:
            try:
                from openai import OpenAI
                self._client = OpenAI(api_key=self.api_key)
            except Exception as e:
                raise RuntimeError(f"OpenAI Provider Initialization Failed: {str(e)}")
        return self._client

    def generate_content(self, prompt: str) -> str:
        if not self._model_name:
            return "Error: OpenAI model not configured. Please set OPENAI_MODEL in .env."
        try:
            response = self.client.chat.completions.create(
                model=self._model_name,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"OpenAI Generation Error: {e}")
            return f"Error: Provider failed to generate content. {str(e)}"

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

class NoLLM(BaseLLM):
    @property
    def model_name(self) -> str:
        return "none"
        
    def generate_content(self, prompt: str) -> str:
        return "No valid LLM API key found. Please configure OpenAI or Gemini in the .env file."
    def get_embedding(self, text: str, task_type: str = "retrieval_document") -> list[float]:
        return [0.0] * 768

def get_llm() -> BaseLLM:
    """
    STRICT ROUTING LOGIC:
    1. If OPENAI_API_KEY is present -> Use OpenAI.
    2. Else if GEMINI_API_KEY is present -> Use Gemini.
    3. If neither -> Return NoLLM with custom message.
    """
    # Prefer OpenAI by default
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key and openai_key != "your_openai_api_key_here" and openai_key.strip():
        try:
            return OpenAILLM()
        except Exception as e:
            # Initialization failure logic
            class ErrorLLM(BaseLLM):
                @property
                def model_name(self) -> str: return "error"
                def generate_content(self, p): return f"OpenAI initialization failed: {str(e)}. Please verify your API key."
                def get_embedding(self, t, k): return [0.0] * 1536
            return ErrorLLM()
    
    # Priority 2: Gemini
    gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if gemini_key and gemini_key.strip():
        try:
            return GoogleLLM()
        except Exception as e:
            # Initialization failure logic
            class ErrorLLM(BaseLLM):
                @property
                def model_name(self) -> str: return "error"
                def generate_content(self, p): return f"Gemini initialization failed: {str(e)}. Please verify your API key."
                def get_embedding(self, t, k): return [0.0] * 768
            return ErrorLLM()

    # Fallback: No key
    return NoLLM()
