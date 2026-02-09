import os
from google.adk.agents import LlmAgent
from .openai_agent import OpenAIAgent

def create_agent(name, description, instruction, tools):
    """
    Factory function to create an agent based on the MODEL_PROVIDER.
    """
    provider = os.getenv("MODEL_PROVIDER", "google").lower()
    
    if provider == "openai":
        return OpenAIAgent(
            name=name,
            description=description,
            instruction=instruction,
            tools=tools
        )
    
    # Default to Gemini/Google
    return LlmAgent(
        name=name,
        description=description,
        model=os.getenv("GEMINI_MODEL_NAME", "gemini-1.5-flash"),
        instruction=instruction,
        tools=tools
    )
