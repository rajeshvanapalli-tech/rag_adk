import os
import json
from core.llm import get_llm, OpenAILLM

class OpenAIAgent:
    def __init__(self, name, description, instruction, tools, llm=None):
        self.name = name
        self.description = description
        self.instruction = instruction
        self.tools = {t.__name__: t for t in tools}
        self.llm = llm if llm else OpenAILLM()
        
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
        import json
        query = new_message.parts[0].text
        
        messages = [
            {"role": "system", "content": self.instruction},
            {"role": "user", "content": query}
        ]
        
        for _ in range(5): # Limit tool call turns
            full_content = ""
            tool_calls = []
            
            # Start a streaming response
            response = self.llm.client.chat.completions.create(
                model=self.llm.model_name,
                messages=messages,
                tools=self.openai_tools,
                tool_choice="auto",
                stream=True
            )
            
            for chunk in response:
                delta = chunk.choices[0].delta
                
                # Handle direct content
                if delta.content:
                    full_content += delta.content
                    class DummyEvent:
                        def __init__(self, text):
                            class Content:
                                def __init__(self, text):
                                    class Part:
                                        def __init__(self, text):
                                            self.text = text
                                    self.parts = [Part(text)]
                            self.content = Content(text)
                    yield DummyEvent(delta.content)
                
                # Handle tool calls (accumulate)
                if delta.tool_calls:
                    for tc_delta in delta.tool_calls:
                        if len(tool_calls) <= tc_delta.index:
                            tool_calls.append({
                                "id": tc_delta.id,
                                "type": "function",
                                "function": {"name": "", "arguments": ""}
                            })
                        
                        target = tool_calls[tc_delta.index]
                        if tc_delta.id: target["id"] = tc_delta.id
                        if tc_delta.function:
                            if tc_delta.function.name:
                                target["function"]["name"] += tc_delta.function.name
                            if tc_delta.function.arguments:
                                target["function"]["arguments"] += tc_delta.function.arguments

            if not tool_calls:
                # Normal completion finished
                return

            # Execute tool calls
            # Prepare assistant message with tool calls for the history
            assistant_msg = {
                "role": "assistant",
                "tool_calls": tool_calls,
                "content": full_content or None
            }
            messages.append(assistant_msg)
            
            for tc in tool_calls:
                tool_name = tc["function"]["name"]
                try:
                    tool_args = json.loads(tc["function"]["arguments"])
                except:
                    tool_args = {"query": tc["function"]["arguments"]} # Fallback
                
                if tool_name in self.tools:
                    print(f"DEBUG: OpenAI calling tool {tool_name} with {tool_args}")
                    result = self.tools[tool_name](**tool_args)
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "name": tool_name,
                        "content": str(result)
                    })
        return
