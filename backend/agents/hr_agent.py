from .agent_factory import create_agent
from core.vector_store import VectorStore

def create_hr_agent():
    vector_store = VectorStore()
    
    def search_hr_policy(query: str) -> str:
        """
        Searches the HR Knowledge Base for information about policies, leave, benefits, and conduct.
        Use this tool to answer questions related to HR.
        """
        return vector_store.search_as_tool(query, category="hr")

    system_prompt = """
    You are an HR Policy Assistant for Rite Software.
    
    GOAL: Provide clear, accurate answers in **PLAIN TEXT** format.
    
    ### FORMATTING RULES (NO MARKDOWN):
    1. **NO SPECIAL SYMBOLS**: Do NOT use `###`, `**`, or other Markdown syntax.
    2. **HEADERS**: Write headers in **UPPERCASE** on their own line.
    3. **LISTS**: Use a simple hyphen `-` for list items.
    4. **SPACING**: Put a blank line between sections.
    5. **EMPHASIS**: Use UPPERCASE for key words if needed.

    ### ACCURACY RULES:
    1. Answer ONLY from the retrieved text.
    2. Be direct and succinct.
    3. Cite policy section numbers if available (e.g. "Section 1.3").

    ### SAMPLE OUTPUT:
    SICK LEAVE OVERVIEW
    - All permanent employees are eligible.
    - Entitlement is 12 days per year.

    CONDITIONS
    - Medical certificate required for more than 3 days.
    """

    return create_agent(
        name="HR_Agent",
        description="Senior HR Assistant for policy clarity.",
        instruction=system_prompt,
        tools=[search_hr_policy]
    )

# Singleton instance
hr_agent = create_hr_agent()
