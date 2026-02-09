import os
import json
from core.llm import get_llm, OpenAILLM

class OpenAIAgent:
    def __init__(self, name, description, instruction, tools):
        self.name = name
        self.description = description
        self.instruction = instruction
        self.tools = {t.__name__: t for t in tools}
        self.llm = OpenAILLM()
        
        # Prepare tool definitions for OpenAI
        self.openai_tools = []
        for tool in tools:
            # Simple conversion of docstrings to OpenAI tool format
            doc = tool.__doc__ or ""
            self.openai_tools.append({
                "type": "function",
                "function": {
                    "name": tool.__name__,
                    "description": doc.strip(),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The search query"
                            }
                        },
                        "required": ["query"]
                    }
                }
            })

    async def run_async(self, user_id, session_id, new_message):
        # new_message is expected to be an object with .parts[0].text
        query = new_message.parts[0].text
        
        messages = [
            {"role": "system", "content": self.instruction},
            {"role": "user", "content": query}
        ]
        
        # Simple tool calling loop
        for _ in range(5): # Limit turns
            response = self.llm.client.chat.completions.create(
                model=self.llm.model_name,
                messages=messages,
                tools=self.openai_tools,
                tool_choice="auto"
            )
            
            msg = response.choices[0].message
            messages.append(msg)
            
            if not msg.tool_calls:
                # No more tools, we have the final answer
                # Yield a dummy event object that main.py expects
                class DummyEvent:
                    def __init__(self, text):
                        class Content:
                            def __init__(self, text):
                                class Part:
                                    def __init__(self, text):
                                        self.text = text
                                self.parts = [Part(text)]
                        self.content = Content(text)
                
                yield DummyEvent(msg.content)
                return

            # Handle tool calls
            for tool_call in msg.tool_calls:
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)
                
                if tool_name in self.tools:
                    print(f"DEBUG: OpenAI calling tool {tool_name} with {tool_args}")
                    result = self.tools[tool_name](**tool_args)
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": tool_name,
                        "content": result
                    })
