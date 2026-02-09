from .agent_factory import create_agent
from core.vector_store import VectorStore

def create_product_agent():
    vector_store = VectorStore()
    
    def search_product_manuals(query: str) -> str:
        """
        Searches the Product Knowledge Base for information about features, specifications, and user manuals.
        Use this tool to answer questions related to products.
        """
        return vector_store.search_as_tool(query, category="product")

    system_prompt = """
    You are a Technical Product Architect.
    Your task is to provide precise, technical, and sequence-aware guidance about our products using the provided manuals.
    
    GUIDELINES:
    1. SEQUENTIAL LOGIC: When explaining steps, ensure the order matches the manual exactly.
    2. TECHNICAL PRECISION: Include button names, navigation paths (e.g., "Menu -> Configuration"), and specific error codes found in the text.
    3. VISUAL CONTEXT: If images are mentioned in the context (e.g. ![Image](/static/...)), use them to explain the UI.
    4. SENTENCE STRUCTURE: Provide sophisticated, well-formed sentences. Ensure high readability.
    5. NO HALLUCINATION: If a step is missing from the retrieved context, do not make it up.
    
    Always use the search_product_manuals tool before answering.
    """

    return create_agent(
        name="Product_Agent",
        description="Technical Architect for precise manual guidance.",
        instruction=system_prompt,
        tools=[search_product_manuals]
    )

# Singleton instance
product_agent = create_product_agent()
