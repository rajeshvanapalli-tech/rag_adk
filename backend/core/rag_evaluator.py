import os
import time
import json
from dotenv import load_dotenv
import google.generativeai as genai
from core.llm import GoogleLLM
from agents.hr_agent import hr_agent
from agents.product_agent import product_agent
from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.genai import types

load_dotenv()

class RAGEvaluator:
    def __init__(self):
        self.llm = GoogleLLM()
        self.session_service = InMemorySessionService()
        
        # Setup Runners
        self.hr_runner = Runner(
            app_name="rag_eval",
            agent=hr_agent,
            session_service=self.session_service,
            auto_create_session=True
        )
        self.product_runner = Runner(
            app_name="rag_eval",
            agent=product_agent,
            session_service=self.session_service,
            auto_create_session=True
        )

    async def get_agent_response(self, category, query):
        runner = self.hr_runner if category == 'hr' else self.product_runner
        full_response = ""
        user_id = f"eval_user_{int(time.time())}"
        session_id = f"eval_session_{category}"
        
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=types.Content(role="user", parts=[types.Part(text=query)])
        ):
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        full_response += part.text
        return full_response

    def judge_score(self, query, context, response):
        """
        Uses Gemini as a judge to score the RAG response.
        """
        prompt = f"""
        You are an impartial judge evaluating a RAG (Retrieval-Augmented Generation) system.
        Evaluate the response based on the query and provided context.
        
        QUERY: {query}
        CONTEXT: {context}
        RESPONSE: {response}
        
        Give a score from 1 to 5 for each of these categories:
        1. Context Relevance: Is the context sufficient to answer the query?
        2. Faithfulness: Does the response only use information from the context?
        3. Answer Relevance: Does the response directly answer the user's query?
        
        Format your output as JSON:
        {{
            "context_relevance": score,
            "faithfulness": score,
            "answer_relevance": score,
            "reasoning": "brief explanation"
        }}
        """
        try:
            raw_eval = self.llm.generate_content(prompt)
            # Cleanup JSON if LLM adds backticks
            if "```json" in raw_eval:
                raw_eval = raw_eval.split("```json")[1].split("```")[0].strip()
            elif "```" in raw_eval:
                raw_eval = raw_eval.split("```")[1].split("```")[0].strip()
            return json.loads(raw_eval)
        except Exception as e:
            return {{"error": str(e)}}

    async def run_evaluation(self, test_cases):
        results = []
        for case in test_cases:
            print(f"Evaluating: {case['query']}")
            # Ideally we'd capture the context from the tool call, for now we assume 
            # retrieval happens and we judge the final output. 
            # To get context, we might need a custom tool wrapper or check session events.
            
            response = await self.get_agent_response(case['category'], case['query'])
            
            # Simple context retrieval for the judge (mocking what the agent saw)
            # In a production setup, we'd extract the actual tool output from the ADK events.
            from core.vector_store import VectorStore
            vs = VectorStore()
            context = vs.search_as_tool(case['query'], category=case['category'])
            
            evaluation = self.judge_score(case['query'], context, response)
            results.append({
                "case": case,
                "response": response,
                "evaluation": evaluation
            })
        return results

if __name__ == "__main__":
    import asyncio
    
    test_cases = [
        {"category": "hr", "query": "What is the standard leave policy?"},
        {"category": "product", "query": "Tell me about the X1 model specifications."}
    ]
    
    evaluator = RAGEvaluator()
    results = asyncio.run(evaluator.run_evaluation(test_cases))
    print(json.dumps(results, indent=2))
