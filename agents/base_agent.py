"""
Base Agent class for DuCO-Agent
All agents inherit from this base class
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime
import time

from state import CaseState, CaseStatus


class BaseAgent(ABC):
    """Base class for all DuCO-Agent agents"""
    
    def __init__(self, agent_id: str, agent_name: str):
        self.agent_id = agent_id
        self.agent_name = agent_name
    
    @abstractmethod
    async def execute(self, case_state: CaseState, **kwargs) -> CaseState:
        """
        Execute the agent's primary function
        
        Args:
            case_state: The shared case state object
            **kwargs: Additional parameters specific to the agent
            
        Returns:
            Updated case_state
        """
        pass
    
    def log_execution(self, case_state: CaseState, input_summary: str, 
                     output_summary: str, duration_ms: float, confidence_score: float = 1.0):
        """Log agent execution to case_state"""
        case_state.add_agent_log(
            agent_id=self.agent_id,
            agent_name=self.agent_name,
            input_summary=input_summary,
            output_summary=output_summary,
            duration_ms=duration_ms,
            confidence_score=confidence_score
        )
    
    def validate_output(self, output: Dict[str, Any], required_fields: list) -> tuple[bool, str]:
        """
        Validate that output contains all required fields
        
        Returns:
            (is_valid, error_message)
        """
        missing_fields = [field for field in required_fields if field not in output or output[field] is None]
        if missing_fields:
            return False, f"Missing required fields: {missing_fields}"
        return True, ""
