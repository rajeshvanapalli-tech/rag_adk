from core.llm import get_llm
from core.vector_store import VectorStore

class BaseAgent:
    def __init__(self, agent_type: str):
        self.agent_type = agent_type
        self.llm = get_llm()
        self.vector_store = VectorStore()

    def get_system_prompt(self) -> str:
        raise NotImplementedError("Subclasses must implement get_system_prompt")

    def ask(self, query: str) -> str:
        # Retrieve context
        # Filter by agent_type (category) to ensure relevant docs
        context_docs = self.vector_store.search(
            query=query, 
            filter_metadata={"category": self.agent_type}
        )
        
        context_text = "\n\n".join(context_docs)
        
        if not context_text:
             context_text = "No specific documents found."

        system_prompt = self.get_system_prompt()
        
        full_prompt = f"""
{system_prompt}

Context Information:
---------------------
{context_text}
---------------------

User Query: {query}

Answer:
"""
        return self.llm.generate_content(full_prompt)
