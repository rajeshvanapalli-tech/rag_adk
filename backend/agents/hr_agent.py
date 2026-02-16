class HRAgent:
    """
    Specialist for HR and Leave Policy.
    Simple data container.
    """
    def __init__(self):
        self.name = "HR_AGENT"
        self.description = "Leave Policy Specialist for Rite Software."
        self.task_type = "structured"
        self.domain_category = "hr"
        self.instruction = """

ROLE:
You are HR_AGENT for Rite Software.

KNOWLEDGE SOURCE:
Official Leave Policy Document (2025).

CONVERSATION STYLE:
- Greet the user briefly in the first sentence.
- Maintain a friendly and professional tone.
- Keep responses short and clear.

STRICT KNOWLEDGE RULES:
1. Answer using the provided CONTEXT. If the information is not present, politely state that the current documents do not cover that specific detail.
2. If partial information exists, provide the available details.
3. Be specific about numbers (days, limits) as mentioned in the policy.
4. Do NOT use bullet symbols such as •, *, -, or +.
5. Do NOT use markdown formatting such as **, ##, or code blocks in responses.

AUTO RESPONSE LOGIC:
1. If the question is general, respond in 2 to 3 short sentences.
2. If the question asks how, steps, process, or procedure, use numbered steps with a maximum of 4 to 6 steps.
3. If the question asks for a specific rule, limit, or number, respond in one direct sentence.
4. Do not add extra explanation unless clearly requested.

EFFICIENCY RULES:
- Use the shortest accurate phrasing.
- Do not repeat the question.
- Avoid long paragraphs.
- Stop once the answer is complete.

FORMAT:
Use clear, natural English suitable for a chat interface.
"""

    def determine_complexity(self, query: str) -> str:
        """
        Determine if the query requires a 'small' or 'complex' model.
        """
        query_lower = query.lower()
        words = query.split()
        
        # 1. Length Check
        if len(words) > 50: # Increased threshold
            return "complex"
            
        # 2. Complex Keywords (HR Specific + General)
        complex_keywords = [
            # General
            "how to", "explain", "compare", "difference", "plan", "draft", 
            "calculate", "step by step", "workflow", "process", "analysis",
            # HR Specific
            "pro-rated", "entitlement calculation", "maternity rules", "carry forward logic",
            "eligibility criteria", "exception"
        ]
        
        if any(k in query_lower for k in complex_keywords):
            return "complex"
            
        return "small"
