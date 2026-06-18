"""
LLM Integration with Anthropic Claude API
Provides reasoning, reflection, and tool-use capabilities
"""

import os
import asyncio
from typing import Dict, Any, Optional, List
from anthropic import Anthropic
from anthropic.types import Message


class ClaudeClient:
    """Wrapper for Anthropic Claude API with enhanced capabilities"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Claude client
        
        Args:
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            print("Warning: ANTHROPIC_API_KEY not set. Using mock mode.")
            self.client = None
            self.mock_mode = True
        else:
            self.client = Anthropic(api_key=self.api_key)
            self.mock_mode = False
    
    async def generate_response(
        self,
        prompt: str,
        system_prompt: str = "",
        max_tokens: int = 4096,
        temperature: float = 0.7,
        tools: Optional[List[Dict]] = None
    ) -> str:
        """
        Generate a response from Claude
        
        Args:
            prompt: User prompt
            system_prompt: System prompt for context
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature
            tools: Optional tool definitions for tool-use
            
        Returns:
            Generated response text
        """
        if self.mock_mode:
            return self._mock_response(prompt, system_prompt)
        
        try:
            message = self.client.messages.create(
                model="claude-3-5-sonnet-20240620",
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt,
                messages=[{"role": "user", "content": prompt}],
                tools=tools if tools else None
            )
            return message.content[0].text
        except Exception as e:
            print(f"Claude API error: {e}")
            return self._mock_response(prompt, system_prompt)
    
    async def reflect(
        self,
        action: str,
        result: str,
        context: str
    ) -> Dict[str, Any]:
        """
        Perform reflection on an action and its result
        
        Args:
            action: Action that was taken
            result: Result of the action
            context: Context in which the action was taken
            
        Returns:
            Reflection analysis with confidence and improvement suggestions
        """
        reflection_prompt = f"""
You are a reflective AI agent. Analyze the following action and its result:

ACTION: {action}
RESULT: {result}
CONTEXT: {context}

Provide your reflection in the following format:
CONFIDENCE: [0.0-1.0]
ANALYSIS: [Your analysis of what went well or poorly]
IMPROVEMENTS: [Specific suggestions for improvement]
SHOULD_RETRY: [true/false if the action should be retried]
"""
        
        response = await self.generate_response(
            reflection_prompt,
            system_prompt="You are a reflective AI agent that analyzes actions and provides constructive feedback."
        )
        
        # Parse the response
        return self._parse_reflection(response)
    
    async def reason(
        self,
        question: str,
        context: str,
        options: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Perform reasoning on a question with given context
        
        Args:
            question: Question to reason about
            context: Context for reasoning
            options: Optional list of options to choose from
            
        Returns:
            Reasoning result with answer and confidence
        """
        reasoning_prompt = f"""
You are a reasoning AI agent. Answer the following question based on the provided context:

QUESTION: {question}
CONTEXT: {context}
"""
        
        if options:
            reasoning_prompt += f"\nOPTIONS: {', '.join(options)}"
        
        reasoning_prompt += """

Provide your answer in the following format:
ANSWER: [Your answer]
CONFIDENCE: [0.0-1.0]
REASONING: [Your step-by-step reasoning]
"""
        
        response = await self.generate_response(
            reasoning_prompt,
            system_prompt="You are a reasoning AI agent that provides well-reasoned answers with confidence scores."
        )
        
        return self._parse_reasoning(response)
    
    async def choose_tool(
        self,
        available_tools: List[Dict[str, Any]],
        task: str,
        context: str
    ) -> Optional[Dict[str, Any]]:
        """
        Choose the best tool for a given task
        
        Args:
            available_tools: List of available tools with descriptions
            task: Task to accomplish
            context: Context for the task
            
        Returns:
            Selected tool or None if no tool is appropriate
        """
        tool_descriptions = "\n".join([
            f"- {tool['name']}: {tool['description']}" 
            for tool in available_tools
        ])
        
        tool_selection_prompt = f"""
You are a tool-selection AI agent. Choose the best tool for the following task:

TASK: {task}
CONTEXT: {context}

AVAILABLE TOOLS:
{tool_descriptions}

Provide your selection in the following format:
SELECTED_TOOL: [tool name or 'none']
REASONING: [Your reasoning for this selection]
CONFIDENCE: [0.0-1.0]
"""
        
        response = await self.generate_response(
            tool_selection_prompt,
            system_prompt="You are a tool-selection AI agent that chooses the most appropriate tool for a given task."
        )
        
        return self._parse_tool_selection(response, available_tools)
    
    def _mock_response(self, prompt: str, system_prompt: str) -> str:
        """Generate mock response when API is not available"""
        return f"[MOCK RESPONSE] Based on the prompt: {prompt[:100]}..."
    
    def _parse_reflection(self, response: str) -> Dict[str, Any]:
        """Parse reflection response"""
        # Simple parsing - in production, use more robust parsing
        lines = response.split('\n')
        result = {
            'confidence': 0.8,
            'analysis': '',
            'improvements': '',
            'should_retry': False
        }
        
        for line in lines:
            if line.startswith('CONFIDENCE:'):
                try:
                    result['confidence'] = float(line.split(':')[1].strip())
                except:
                    pass
            elif line.startswith('ANALYSIS:'):
                result['analysis'] = line.split(':', 1)[1].strip()
            elif line.startswith('IMPROVEMENTS:'):
                result['improvements'] = line.split(':', 1)[1].strip()
            elif line.startswith('SHOULD_RETRY:'):
                result['should_retry'] = 'true' in line.lower()
        
        return result
    
    def _parse_reasoning(self, response: str) -> Dict[str, Any]:
        """Parse reasoning response"""
        lines = response.split('\n')
        result = {
            'answer': '',
            'confidence': 0.8,
            'reasoning': ''
        }
        
        for line in lines:
            if line.startswith('ANSWER:'):
                result['answer'] = line.split(':', 1)[1].strip()
            elif line.startswith('CONFIDENCE:'):
                try:
                    result['confidence'] = float(line.split(':')[1].strip())
                except:
                    pass
            elif line.startswith('REASONING:'):
                result['reasoning'] = line.split(':', 1)[1].strip()
        
        return result
    
    def _parse_tool_selection(self, response: str, available_tools: List[Dict]) -> Optional[Dict]:
        """Parse tool selection response"""
        lines = response.split('\n')
        selected_tool_name = None
        
        for line in lines:
            if line.startswith('SELECTED_TOOL:'):
                selected_tool_name = line.split(':', 1)[1].strip().lower()
                break
        
        if selected_tool_name == 'none':
            return None
        
        # Find the tool
        for tool in available_tools:
            if tool['name'].lower() == selected_tool_name:
                return tool
        
        return None
