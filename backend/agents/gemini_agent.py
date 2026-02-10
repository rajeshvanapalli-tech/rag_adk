import os
import json
import time
from core.llm import GoogleLLM

class GeminiAgent:
    def __init__(self, name, description, instruction, tools, llm=None):
        self.name = name
        self.description = description
        self.instruction = instruction
        self.tools = {t.__name__: t for t in tools}
        self.llm = llm if llm else GoogleLLM()
        
        # Prepare tools for Gemini (SDK handles this differently, but we use the same tools)
        self.gemini_tools = [t for t in tools]

    async def run_async(self, user_id, session_id, new_message):
        import google.generativeai as genai
        query = new_message.parts[0].text
        
        # Initialize history with system instruction
        # Ideally this would be system_instruction in GenerativeModel, but history works too
        history = [
            {"role": "user", "parts": [self.instruction]},
            {"role": "model", "parts": ["I understand. I will provide short, numbered responses based only on the context."]},
            {"role": "user", "parts": [query]}
        ]
        
        for _ in range(5): # Turns for tool calls
            response = self.llm.model.generate_content(
                history,
                tools=self.gemini_tools,
                stream=True
            )
            
            full_text = ""
            accumulated_parts = []
            tool_calls = []
            
            for chunk in response:
                if chunk.candidates:
                    for part in chunk.candidates[0].content.parts:
                        accumulated_parts.append(part)
                        if part.text:
                            full_text += part.text
                            
                            class DummyEvent:
                                def __init__(self, text):
                                    class Content:
                                        def __init__(self, text):
                                            class Part:
                                                def __init__(self, text):
                                                    self.text = text
                                            self.parts = [Part(text)]
                                    self.content = Content(text)
                            
                            yield DummyEvent(part.text)
                            
                        if part.function_call:
                            tool_calls.append(part.function_call)

            if not tool_calls:
                return # Done

            # Add model's full response (with tool calls) to history
            history.append({"role": "model", "parts": accumulated_parts})
            
            # Execute tool calls
            function_responses = []
            for fc in tool_calls:
                tool_name = fc.name
                tool_args = {k: v for k, v in fc.args.items()}
                
                if tool_name in self.tools:
                    print(f"DEBUG: Gemini calling tool {tool_name} with {tool_args}")
                    result = self.tools[tool_name](**tool_args)
                    
                    function_responses.append(
                        genai.protos.Part(
                            function_response=genai.protos.FunctionResponse(
                                name=tool_name,
                                response={'result': str(result)}
                            )
                        )
                    )
            
            # Add all function responses as one 'function' role message
            if function_responses:
                history.append({"role": "function", "parts": function_responses})
        return
