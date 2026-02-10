import os
from google.adk.agents import LlmAgent
from .openai_agent import OpenAIAgent

from core.llm import get_llm, OpenAILLM, GoogleLLM

def create_agent(name, description, instruction, tools):
    """
    Factory function to create an agent based STRICTLY on environment configuration.
    """
    llm = get_llm()
    
    if isinstance(llm, OpenAILLM):
        return OpenAIAgent(
            name=name,
            description=description,
            instruction=instruction,
            tools=tools,
            llm=llm
        )
    
    # Default to Gemini/Google ADK native agent
    return LlmAgent(
        name=name,
        description=description,
        model=llm.model_name,
        instruction=instruction,
        tools=tools
    )
