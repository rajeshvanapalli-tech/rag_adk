import os
import base64
import mimetypes
import google.generativeai as genai
from openai import OpenAI
from dotenv import load_dotenv
import PIL.Image

load_dotenv()

class ImageProcessor:
    def __init__(self):
        self.active_provider = os.getenv("ACTIVE_LLM_PROVIDER", "auto").lower()
        self.gemini_key = os.getenv("GEMINI_API_KEY")
        self.openai_key = os.getenv("OPENAI_API_KEY")
        
        # Initialize Gemini
        self.gemini_model = None
        if self.gemini_key:
            try:
                genai.configure(api_key=self.gemini_key)
                # Use flash for speed/cost unless specified otherwise
                model_name = os.getenv("GEMINI_SMALL_MODEL", "gemini-1.5-flash")
                self.gemini_model = genai.GenerativeModel(model_name)
            except Exception as e:
                print(f"Failed to initialize Gemini for images: {e}")

        # Initialize OpenAI
        self.openai_client = None
        if self.openai_key:
            try:
                self.openai_client = OpenAI(api_key=self.openai_key)
                self.openai_model = os.getenv("OPENAI_SMALL_MODEL", "gpt-4o-mini")
            except Exception as e:
                print(f"Failed to initialize OpenAI for images: {e}")

    def _encode_image(self, image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    def generate_description(self, image_path: str) -> str:
        """
        Generates a description using the active provider.
        """
        if not os.path.exists(image_path):
            return f"Image not found at {image_path}"

        # Determine provider priority
        provider = self.active_provider
        
        # If auto, prefer OpenAI if available (often robust for vision), else Gemini
        if provider == "auto":
            if self.gemini_model:
                provider = "gemini"
                print("ImageProcessor: Auto-selecting Gemini (Priority)")
            elif self.openai_client:
                provider = "openai"
                print("ImageProcessor: Auto-selecting OpenAI (Fallback)")
            else:
                return "No AI provider configured for image processing."
        
        # Execute based on priority: Gemini -> OpenAI
        if provider == "gemini" or (provider == "auto" and self.gemini_model):
            try:
                return self._process_gemini(image_path)
            except Exception as e:
                print(f"Gemini processing failed: {e}. Trying OpenAI fallback...")
                if self.openai_client:
                    return self._process_openai(image_path)
                return f"Gemini failed and no OpenAI fallback: {str(e)}"
        
        elif provider == "openai" or (provider == "auto" and self.openai_client):
            try:
                return self._process_openai(image_path)
            except Exception as e:
                 print(f"OpenAI processing failed: {e}. Trying Gemini (if available)...")
                 if self.gemini_model:
                     return self._process_gemini(image_path)
                 return f"OpenAI failed: {str(e)}"

        return "Image processing unavailable (Check API keys)."

    def _process_gemini(self, image_path):
        try:
            img = PIL.Image.open(image_path)
            prompt = (
                "Analyze this image for a RAG knowledge base. "
                "Describe the visual content in detail. "
                "If it contains text, charts, or steps, transcribe and explain them clearly."
            )
            response = self.gemini_model.generate_content([prompt, img])
            return response.text.strip() if response and response.text else "No description."
        except Exception as e:
             raise RuntimeError(f"Gemini processing failed: {e}")

    def _process_openai(self, image_path):
        try:
            base64_image = self._encode_image(image_path)
            
            # Simple mimetype guess
            mime_type, _ = mimetypes.guess_type(image_path)
            if not mime_type: mime_type = "image/jpeg"
            
            prompt = "Describe this image in detail for a technical knowledge base. Extract text, data points, and explain workflows if present."
            
            response = self.openai_client.chat.completions.create(
                model=self.openai_model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{mime_type};base64,{base64_image}",
                                    "detail": "auto" 
                                }
                            },
                        ],
                    }
                ],
                max_tokens=600,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            raise RuntimeError(f"OpenAI processing failed: {e}")


    async def generate_description_async(self, image_path: str) -> str:
        """
        Generates a description using the active provider asynchronously
        by offloading the blocking call to a thread.
        """
        import asyncio
        return await asyncio.to_thread(self.generate_description, image_path)

# Singleton instance
image_processor = ImageProcessor()
