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
    def __init__(self, model_name: str, temperature: float, max_tokens: int):
        from google import genai
        self.api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        self._model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY or GOOGLE_API_KEY missing in .env")
        
        try:
            self.client = genai.Client(api_key=self.api_key)
            self.embedding_model = os.getenv("GEMINI_EMBEDDING_MODEL")
            if not self.embedding_model:
                raise ValueError("GEMINI_EMBEDDING_MODEL missing in .env")
        except Exception as e:
            raise RuntimeError(f"Google GenAI Provider (Modern) Initialization Failed: {str(e)}")

    @property
    def model_name(self) -> str:
        return self._model_name

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
        from google.genai import types
        try:
            config = types.GenerateContentConfig(
                temperature=self.temperature,
                max_output_tokens=self.max_tokens
            )
            response = self._retry_on_429(
                self.client.models.generate_content,
                model=self._model_name,
                contents=prompt,
                config=config
            )
            if not response or not response.text:
                return "I'm sorry, I couldn't generate a response."
            return response.text
        except Exception as e:
            print(f"LLM Generation Error (Modern): {e}")
            return f"Error: Provider failed to generate content. {str(e)}"

    def get_embedding(self, text: str, task_type: str = "retrieval_document") -> list[float]:
        """Gets embedding for a single text or a list of texts (batch)."""
        from google.genai import types
        try:
            is_batch = isinstance(text, list)
            input_texts = text if is_batch else [text]
            
            # task_type name varies in modern SDK: RETRIEVAL_DOCUMENT vs retrieval_document
            config = types.EmbedContentConfig(task_type=task_type.upper())
            
            result = self._retry_on_429(
                self.client.models.embed_content,
                model=self.embedding_model,
                contents=input_texts,
                config=config
            )
            
            # result.embeddings is a list of Embedding objects
            # each has a 'values' field containing the floats
            embeddings = [emb.values for emb in result.embeddings]
            return embeddings if is_batch else embeddings[0]

        except Exception as e:
            print(f"CRITICAL: Modern Embedding Failed for model {self.embedding_model}: {e}")
            # HARDCODED DIMENSIONS:
            # gemini-embedding-001 -> 3072
            # text-embedding-004 -> 768
            dim = 3072 if "gemini-embedding-001" in str(self.embedding_model) else 768
            
            if isinstance(text, list):
                return [[0.0] * dim for _ in text]
            return [0.0] * dim

class OpenAILLM(BaseLLM):
    def __init__(self, model_name: str, temperature: float, max_tokens: int):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self._model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        # Embedding model from env or error
        self.embedding_model = os.getenv("OPENAI_EMBEDDING_MODEL")
        if not self.embedding_model:
             raise ValueError("OPENAI_EMBEDDING_MODEL missing in .env")
             
        self._client = None
        
        if not self.api_key or self.api_key == "your_openai_api_key_here":
            raise ValueError("OPENAI_API_KEY missing in .env")

    @property
    def model_name(self) -> str:
        return self._model_name

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
            return "Error: OpenAI model not configured."
        try:
            response = self.client.chat.completions.create(
                model=self._model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"OpenAI Generation Error: {e}")
            return f"Error: Provider failed to generate content. {str(e)}"

    def get_embedding(self, text: str, task_type: str = "retrieval_document") -> list[float]:
        """Gets embedding for a single text or a list of texts (batch)."""
        try:
            is_batch = isinstance(text, list)
            input_texts = text if is_batch else [text]
            
            response = self.client.embeddings.create(
                input=input_texts,
                model=self.embedding_model
            )
            
            embeddings = [data.embedding for data in response.data]
            return embeddings if is_batch else embeddings[0]
            
        except Exception as e:
            print(f"OpenAI Embedding Error: {e}")
            # text-embedding-3-small is 1536, text-embedding-ada-002 is 1536
            dim = 1536 
            if isinstance(text, list):
                return [[0.0] * dim for _ in text]
            return [0.0] * dim

class NoLLM(BaseLLM):
    @property
    def model_name(self) -> str:
        return "none"
        
    def generate_content(self, prompt: str) -> str:
        return "No valid LLM API key found. Please configure OpenAI or Gemini in the .env file."
    def get_embedding(self, text: str, task_type: str = "retrieval_document") -> list[float]:
        return [0.0] * 3072

class FallbackLLM(BaseLLM):
    def __init__(self, primary: BaseLLM, secondary: BaseLLM):
        self.primary = primary
        self.secondary = secondary

    @property
    def model_name(self) -> str:
        return f"{self.primary.model_name} (with fallback)"

    def generate_content(self, prompt: str) -> str:
        try:
            response = self.primary.generate_content(prompt)
            if "Error:" in response or "initialization failed" in response:
                 raise RuntimeError(response)
            return response
        except Exception as e:
            print(f"Primary LLM ({self.primary.model_name}) failed: {e}. Trying fallback...")
            try:
                return self.secondary.generate_content(prompt)
            except Exception as e2:
                return f"All LLM providers failed. Primary: {e}, Fallback: {e2}"

    def get_embedding(self, text: str, task_type: str = "retrieval_document") -> list[float]:
        try:
            return self.primary.get_embedding(text, task_type)
        except Exception as e:
            print(f"Primary embedding failed, trying fallback: {e}")
            try:
                return self.secondary.get_embedding(text, task_type)
            except Exception:
                # Last resort fallback to zero vector
                return self.primary.get_embedding(text, task_type) # This will return the zero vector from primary

def get_llm(provider: str = None, task_type: str = "normal", complexity: str = "small") -> BaseLLM:
    """
    Centralized LLM factory. complexity: 'small' or 'complex'.
    All model names, temperatures, and tokens are strictly from .env.
    """
    env_active_provider = os.getenv("ACTIVE_LLM_PROVIDER", "auto").lower()
    suffix = "SMALL" if complexity == "small" else "COMPLEX"

    def get_config(p_name):
        base = p_name.upper()
        model = os.getenv(f"{base}_{suffix}_MODEL")
        temp = os.getenv(f"{base}_TEMPERATURE_{suffix}")
        tokens = os.getenv(f"{base}_MAX_TOKENS_{suffix}")
        
        if not model:
            raise ValueError(f"CRITICAL: {base}_{suffix}_MODEL missing in .env")
        
        return {
            "model": model,
            "temp": float(temp) if temp else 0.5,
            "tokens": int(tokens) if tokens else 1500
        }

    gemini_config = get_config("GEMINI")
    openai_config = get_config("OPENAI")

    has_openai = bool(os.getenv("OPENAI_API_KEY")) and os.getenv("OPENAI_API_KEY") != "your_openai_key_here"
    has_gemini = bool(os.getenv("GEMINI_API_KEY")) or bool(os.getenv("GOOGLE_API_KEY"))

    selected_provider = provider if provider and provider != "auto" else env_active_provider
    if selected_provider == "auto":
        selected_provider = "gemini" if has_gemini else ("openai" if has_openai else "none")

    def create_instance(p):
        if p == "openai" and has_openai:
            return OpenAILLM(
                model_name=openai_config["model"],
                temperature=openai_config["temp"],
                max_tokens=openai_config["tokens"]
            )
        if p == "gemini" and has_gemini:
            return GoogleLLM(
                model_name=gemini_config["model"],
                temperature=gemini_config["temp"],
                max_tokens=gemini_config["tokens"]
            )
        return None

    primary = create_instance(selected_provider)
    
    if primary:
        provider_name = "OPENAI" if selected_provider == "openai" else "GOOGLE GEMINI"
        print(f"[LLM] Activating Provider: {provider_name} | Model: {primary.model_name}")
    
    secondary = create_instance("openai" if selected_provider == "gemini" else "gemini")

    if not primary:
        return secondary if secondary else NoLLM()
    
    return FallbackLLM(primary, secondary) if secondary else primary
