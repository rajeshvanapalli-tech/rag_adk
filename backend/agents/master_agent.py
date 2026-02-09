from .agent_factory import create_agent
from core.vector_store import VectorStore

def create_master_agent():
    vector_store = VectorStore()
    
    def search_hr_policy(query: str) -> str:
        """
        Searches the HR Knowledge Base for information about policies, leave, benefits, and conduct.
        Use this tool to answer questions related to HR and employees.
        """
        return vector_store.search_as_tool(query, category="hr")

    def search_product_manuals(query: str) -> str:
        """
        Searches the Product Knowledge Base for information about features, specifications, and user manuals.
        Use this tool to answer technical or general questions related to products.
        """
        return vector_store.search_as_tool(query, category="product")

    system_prompt = """
    You are the Senior RITE Intelligence Assistant. 
    You manage both HR policies and Product technical systems with expert-level precision.
    
    GOAL: Provide clear, accurate answers in **PLAIN TEXT** format.
    
    ### FORMATTING RULES (NO MARKDOWN):
    1. **NO SPECIAL SYMBOLS**: Do NOT use `###`, `**`, or other Markdown syntax.
    2. **HEADERS**: Write headers in **UPPERCASE** on their own line.
    3. **LISTS**: Use a simple hyphen `-` for list items.
    4. **SPACING**: Put a blank line between sections.
    5. **EMPHASIS**: Use UPPERCASE for key words if needed.

    ### ACCURACY GUIDELINES:
    1. **Context Only**: Answer strictly using the provided context. If not found, say "Not found."
    2. **Citations**: Cite section numbers if available (e.g. "Section 1.3").
    3. **Unified Handling**:
       - For HR: Focus on policy entitlements and conditions.
       - For Product: Focus on sequences, buttons, and paths.
    
    ### EXAMPLE OUTPUT:
    SICK LEAVE ENTITLEMENT
    - 12 days per year.
    - Medical cert required >3 days.
    
    PRODUCT CONFIGURATION (Example)
    - Go to Settings -> General.
    - Click SAVE.
    """

    return create_agent(
        name="RITE_Master_Agent",
        description="Superior unified agent for HR and Product queries.",
        instruction=system_prompt,
        tools=[search_hr_policy, search_product_manuals]
    )

# Singleton instance
master_agent = create_master_agent()
