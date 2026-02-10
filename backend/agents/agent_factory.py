from .openai_agent import OpenAIAgent
from .gemini_agent import GeminiAgent
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
    
    if isinstance(llm, GoogleLLM):
        return GeminiAgent(
            name=name,
            description=description,
            instruction=instruction,
            tools=tools,
            llm=llm
        )
    
    # Fallback/Default
    return GeminiAgent(
        name=name,
        description=description,
        instruction=instruction,
        tools=tools
    )
