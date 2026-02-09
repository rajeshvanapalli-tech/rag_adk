from core.llm import get_llm

class MasterRouter:
    def __init__(self):
        self.llm = get_llm()

    def classify_intent(self, query: str, history: list[str] = []) -> str:
        """
        Classifies the user query into 'hr' or 'product' or 'ambiguous'.
        Uses history to understand context.
        """
        history_text = "\n".join(history[-3:]) if history else "No previous context."
        
        prompt = f"""
        You are a Master Router Agent. Your job is to classify the user's intent into one of two domains: 'hr' or 'product'.

        Domains:
        - 'hr': Questions about HR policies, employee data, leave, payroll, benefits, onboarding, compliance, code of conduct.
        - 'product': Questions about product details, features, specifications, pricing, documentation, troubleshooting, usage, installation.

        Context:
        {history_text}

        User Query: {query}

        Instructions:
        - Analyze the user query and the context.
        - If the query is clearly about HR, return 'hr'.
        - If the query is clearly about Product, return 'product'.
        - If the query is greeting or general conversation (e.g. "hi", "thanks"), look at the context. If context is empty, default to 'hr' (as a safe default) or return 'general' if you want a generic response (but for now return 'hr' or 'product' based on likely intent). Let's default greetings to 'hr' to start.
        - If the query is completely ambiguous and requires clarification, return 'ambiguous'.

        Return ONLY single word: 'hr', 'product', or 'ambiguous'.
        """
        
        response = self.llm.generate_content(prompt).strip().lower()
        
        # Fallback for safety
        if "hr" in response:
            return "hr"
        elif "product" in response:
            return "product"
        else:
            return "ambiguous"

    def clarify_intent(self, query: str) -> str:
        """
        Generates a clarification question when the intent is ambiguous.
        """
        prompt = f"""
        The user asked: "{query}"
        This query is ambiguous. Generate a polite question to ask the user to clarify if they are asking about HR policies or Product details.
        Keep it short.
        """
        return self.llm.generate_content(prompt).strip()
