from typing import Any, List, Optional
from pydantic import Field, ConfigDict, PrivateAttr
from .hr_agent import HRAgent
from .product_agent import ProductAgent
from .general_agent import GeneralAgent
from core.llm import get_llm, OpenAILLM, GoogleLLM
from core.vector_store import VectorStore
from google.adk.agents import Agent
from google.adk.events.event import Event
from google.genai import types # Framework Communication Protocol

class MasterAgent(Agent):
    """
    RITE AI Master Agent - Dual Engine (Gemini & OpenAI)
    Built on Google ADK Framework.
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)

    # Required Agent Fields for ADK compliance
    name: str = "MASTER_AGENT"
    description: str = "Master Controller for Rite Software AI System."
    instruction: str = "You are the RITE AI Master Agent, coordinating between specialist agents."

    # Internal state (Not Pydantic fields)
    _hr_agent: Any = PrivateAttr()
    _product_agent: Any = PrivateAttr()
    _general_agent: Any = PrivateAttr()
    _vector_store: Any = PrivateAttr()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        print("[MasterAgent] Initializing internal specialist agents...")
        self._hr_agent = HRAgent()
        self._product_agent = ProductAgent()
        self._general_agent = GeneralAgent()
        self._vector_store = VectorStore()
        print("[MasterAgent] Initialization Complete.")

    @property
    def vector_store(self):
        return self._vector_store

    @property
    def hr_agent(self):
        return self._hr_agent

    @property
    def product_agent(self):
        return self._product_agent

    @property
    def general_agent(self):
        return self._general_agent
    def detect_intents(self, query: str):
        """
        Detects all relevant domains for the query using Semantic LLM Routing.
        Returns a list of agents.
        """
        try:
            # Use a fast, small model for routing (low latency)
            # We use a dedicated task_type to ensure it's treated as a system instruction
            router_llm = get_llm(complexity="small", task_type="classification")
            
            prompt = f"""
            You are an expert intent classifier for an enterprise rag system.
            Classify the following query into the correct domain(s).
            
            1. HR: (Leaves, holidays, policies, attendance, salary, benefits, office timings, manager queries)
            2. PRODUCT: (ConvertRite, Oracle, clouds, pods, mappings, SQL, FBDI, HDL, templates, metadata, migrations, technical errors, validation, loading)
            
            Instructions:
            - Analyze the semantic meaning, not just keywords.
            - "How many leaves can I take in a sequence" -> HR (it's about consecutive days).
            - "How to create a database sequence" -> PRODUCT.
            - If it applies to both, return "HR, PRODUCT".
            - If it's a general greeting or irrelevant to business, return "GENERAL".
            
            Query: "{query}"
            
            Return ONLY the category name(s).
            """
            
            # Fast generation
            response = router_llm.generate_content(prompt).strip().upper()
            print(f"[MasterAgent] Router Analysis: {response}")
            
            selected_agents = []
            if "HR" in response:
                selected_agents.append(self._hr_agent)
            if "PRODUCT" in response:
                selected_agents.append(self._product_agent)
                
            # If router says GENERAL or returns nothing valid, check if we should default to General
            # But typically we trust the router. Default to General.
            if not selected_agents:
                selected_agents.append(self._general_agent)
                
            return selected_agents

        except Exception as e:
            print(f"[MasterAgent] Semantic Routing Failed: {e}. Falling back to keywords.")
            return self._fallback_keyword_detection(query)

    def _fallback_keyword_detection(self, query: str):
        """Original keyword-based detection for resilience."""
        query_lower = query.lower()
        selected_agents = []

        # HR Keywords
        hr_keywords = [
            "leave", "sick", "casual", "earned", "maternity", "paternity",
            "lop", "notice period", "holiday", "entitlement", "policy", "attendance"
        ]

        # Product Keywords
        product_keywords = [
            "convert", "pod", "parent object", "child object",
            "metadata", "mapping", "formula", "sequence", "validation",
            "reconciliation", "load", "fbdi", "hdl", "import", "template workbench"
        ]
        
        if any(k in query_lower for k in hr_keywords):
            selected_agents.append(self._hr_agent)
            
        if any(k in query_lower for k in product_keywords) or "project" in query_lower:
            selected_agents.append(self._product_agent)
            
        if not selected_agents:
            selected_agents.append(self._general_agent)
            
        return selected_agents

    async def run_async(self, ctx):
        """
        Main execution flow:
        User -> MasterAgent -> detect_intents -> gather context for all -> generate unified response
        """
        user_id = ctx.session.user_id
        session_id = ctx.session.id
        
        # In newer ADK versions, new_message is passed as user_content in the context
        new_message = getattr(ctx, 'user_content', getattr(ctx, 'new_message', None))

        print(f"[MasterAgent] run_async started for session: {session_id}")
        
        # Imports for handling context images
        import re
        import os
        
        # 1. Extract User Question
        user_question = ""
        if new_message:
            if hasattr(new_message, 'parts') and new_message.parts:
                user_question = new_message.parts[0].text
            else:
                user_question = str(new_message)
        
        print(f"[MasterAgent] User Question: {user_question}")
        
        # 2. Detect Intents (Multi-agent support)
        selected_agents = self.detect_intents(user_question)
        print(f"[MasterAgent] Selected Agents: {[a.name for a in selected_agents]}")
        
        # 3. Retrieve Context from for all agents
        # If multiple agents, we gather context for each domain
        all_contexts = []
        for agent in selected_agents:
            print(f"[MasterAgent] Fetching context for category: {agent.domain_category}")
            context = self._vector_store.search_as_tool(
                query=user_question, 
                category=agent.domain_category
            )
            if "No relevant information" not in context:
                all_contexts.append(f"[{agent.domain_category.upper()} CONTEXT]:\n{context}")
        
        context_text = "\n\n".join(all_contexts) if all_contexts else "No relevant knowledge found."
        print(f"[MasterAgent] Context retrieved (length: {len(context_text)})")
        
        # 4. Determine Complexity (highest common denominator)
        complexity = "small"
        for agent in selected_agents:
            if hasattr(agent, 'determine_complexity') and agent.determine_complexity(user_question) == "complex":
                complexity = "complex"
                break
        
        llm = get_llm(
            task_type="unified_response",
            complexity=complexity
        )
        print(f"[MasterAgent] Intents: {[a.name for a in selected_agents]}, Model: {llm.model_name}")
        
        # 5. Construct Unified Prompt
        # Combine instructions from all relevant agents
        agent_instructions = "\n\n".join([a.instruction for a in selected_agents])
        full_prompt = (
            f"SYSTEM ROLE:\n{agent_instructions}\n\n"
            f"Combined Knowledge Context:\n{context_text}\n\n"
            f"USER QUESTION:\n{user_question}\n\n"
            f"Final Instructions:\n"
            f"1. Address ALL parts of the user question.\n"
            f"2. Use the relevant domain context (HR or Product or Both).\n"
            f"3. If one part of the question is not in context, answer the part that IS and state that you have limited details on the other."
        )
        
        # 6. Generate Content
        # 6. Generate Content
        try:
            # Construct multimodal prompt if images exist
            final_content = [types.Part(text=full_prompt)]
            
            # Add back any image parts from the original message
            if new_message and hasattr(new_message, 'parts'):
                for part in new_message.parts:
                    if part.inline_data:
                        final_content.append(part)
            
            # Extract and attach images from the RAG context
            # Regex to find ![Image](/static/images/filename)
            image_matches = re.findall(r'!\[Image\]\(/static/images/([^)]+)\)', context_text)
            unique_images = list(set(image_matches))
            
            if unique_images:
                print(f"[MasterAgent] Found {len(unique_images)} images in context. Attaching top 3...")
                
            for img_name in unique_images[:3]: # Limit to avoid overloading
                img_path = os.path.join("static", "images", img_name)
                if os.path.exists(img_path):
                    try:
                        with open(img_path, "rb") as img_file:
                            img_bytes = img_file.read()
                            
                        # Guess mime type
                        ext = os.path.splitext(img_name)[1].lower()
                        mime_type = "image/png"
                        if ext in ['.jpg', '.jpeg']: mime_type = "image/jpeg"
                        elif ext == '.webp': mime_type = "image/webp"
                        
                        final_content.append(types.Part(
                            inline_data=types.Blob(
                                mime_type=mime_type,
                                data=img_bytes
                            )
                        ))
                    except Exception as e:
                        print(f"[MasterAgent] Failed to load metadata image {img_name}: {e}")
            
            if unique_images:
                 final_content[0].text += "\n\n[SYSTEM]: Relevant images from the documents have been attached to this request for your reference."

            response_text = llm.generate_content(final_content)
        except Exception as e:
            response_text = f"Error generating response: {str(e)}"
        # 7. Return Final Response
        # We wrap the response in ADK 'types' so the Framework (Runner) 
        # can process it consistently, regardless of whether it came from OpenAI or Google.
        final_content = types.Content(
            role='model',
            parts=[types.Part(text=response_text)]
        )
        
        print(f"[MasterAgent] Yielding response (length: {len(response_text)})")
        yield Event(
            content=final_content,
            author=llm.model_name
        )

# Singleton instance
master_agent = MasterAgent()

def create_master_agent():
    return master_agent
