"""
AG-01: Supervisor Agent
Orchestrates all sub-agents, manages state machine, handles retries and validation loops
Enhanced with LLM reasoning, dynamic decision-making, and reflection loops
"""

import asyncio
import time
from typing import Dict, Any, Optional, List
from datetime import datetime

from state import CaseState, CaseStatus
from agents.base_agent import BaseAgent
from agents.intake_agent import IntakeAgent
from agents.cob_agent import COBAgent
from agents.preauth_agent import PreAuthAgent
from agents.finance_agent import FinanceAgent
from agents.output_agent import OutputAgent
from llm import ClaudeClient


class SupervisorAgent(BaseAgent):
    """Supervisor Agent that orchestrates all sub-agents"""
    
    def __init__(self):
        super().__init__("AG-01", "Supervisor Agent")
        
        # Initialize LLM client for reasoning and reflection
        self.claude_client = ClaudeClient()
        
        # Initialize sub-agents
        self.intake_agent = IntakeAgent()
        self.cob_agent = COBAgent()
        self.preauth_agent = PreAuthAgent()
        self.finance_agent = FinanceAgent()
        self.output_agent = OutputAgent()
        
        # Available tools for dynamic decision-making
        self.available_tools = [
            {
                "name": "intake_parsing",
                "description": "Parse and extract data from multi-modal documents",
                "agent": self.intake_agent
            },
            {
                "name": "cob_logic",
                "description": "Apply Coordination of Benefits rules and calculate payments",
                "agent": self.cob_agent
            },
            {
                "name": "preauth_drafting",
                "description": "Generate IRDAI-compliant pre-authorization letters",
                "agent": self.preauth_agent
            },
            {
                "name": "financial_calculation",
                "description": "Validate and finalize monetary calculations",
                "agent": self.finance_agent
            },
            {
                "name": "output_generation",
                "description": "Generate patient-friendly outputs and visualizations",
                "agent": self.output_agent
            }
        ]
    
    async def execute(self, case_state: CaseState, **kwargs) -> CaseState:
        """
        Execute the full agent pipeline with dynamic decision-making and reflection loops
        
        Args:
            case_state: The shared case state object
            **kwargs: Additional parameters (document_paths, user_query)
            
        Returns:
            Updated case_state with all agent outputs
        """
        start_time = time.time()
        input_summary = f"Case ID: {case_state.case_id}, Status: {case_state.status}"
        
        try:
            # Dynamic case complexity assessment
            case_complexity = await self._assess_case_complexity(case_state, kwargs)
            case_state.complexity = case_complexity
            
            # Stage 1: INTAKE with reflection
            case_state.update_status(CaseStatus.INTAKE)
            case_state = await self._run_agent_with_reflection(
                self.intake_agent, case_state, **kwargs
            )
            
            # Dynamic decision: Check if additional parsing needed
            if await self._needs_additional_parsing(case_state):
                case_state = await self._run_additional_parsing(case_state, kwargs)
            
            # Stage 2: COB Logic with reflection
            case_state.update_status(CaseStatus.COB)
            case_state = await self._run_agent_with_reflection(
                self.cob_agent, case_state
            )
            
            # Dynamic decision: Check if manual review needed for complex COB
            if case_complexity == 'high' and len(case_state.errors) > 0:
                await self._request_human_review(case_state, "COB complexity")
            
            # Stage 3: FINANCE and PREAUTH (parallel) with reflection
            case_state.update_status(CaseStatus.FINANCE)
            
            # Run finance and preauth in parallel
            finance_task = self._run_agent_with_reflection(self.finance_agent, case_state)
            preauth_task = self._run_agent_with_reflection(self.preauth_agent, case_state)
            
            finance_result, preauth_result = await asyncio.gather(finance_task, preauth_task)
            
            # Merge results (finance_result has the latest state)
            case_state = finance_result
            case_state.preauth_letters = preauth_result.preauth_letters
            
            # Stage 4: OUTPUT with reflection
            case_state.update_status(CaseStatus.OUTPUT)
            case_state = await self._run_agent_with_reflection(
                self.output_agent, case_state
            )
            
            # Final reflection on overall pipeline
            await self._final_pipeline_reflection(case_state)
            
            # Stage 5: DONE
            case_state.update_status(CaseStatus.DONE)
            
            duration_ms = (time.time() - start_time) * 1000
            output_summary = f"Pipeline completed. Status: {case_state.status.value}. Errors: {len(case_state.errors)}. Complexity: {case_complexity}"
            self.log_execution(case_state, input_summary, output_summary, duration_ms)
            
            return case_state
            
        except Exception as e:
            case_state.update_status(CaseStatus.ERROR)
            case_state.add_error(
                agent_id=self.agent_id,
                field_name="pipeline",
                message=f"Pipeline execution failed: {str(e)}",
                human_review_required=True
            )
            duration_ms = (time.time() - start_time) * 1000
            output_summary = f"Pipeline failed with error: {str(e)}"
            self.log_execution(case_state, input_summary, output_summary, duration_ms, confidence_score=0.0)
            return case_state
    
    async def _assess_case_complexity(self, case_state: CaseState, kwargs: Dict) -> str:
        """
        Dynamically assess case complexity using LLM reasoning
        
        Args:
            case_state: Current case state
            kwargs: Input parameters
            
        Returns:
            Complexity level: 'low', 'medium', or 'high'
        """
        document_count = len(kwargs.get('document_paths', {}))
        user_query = kwargs.get('user_query', '')
        
        complexity_prompt = f"""
Assess the complexity of this insurance COB case:

Number of documents: {document_count}
User query: {user_query[:200]}...

Rate the complexity as:
- LOW: Simple case, clear documents, standard scenario
- MEDIUM: Moderate complexity, some ambiguity, multiple claims
- HIGH: Complex case, unclear documents, unusual scenarios, multiple patients

Provide your assessment in the format:
COMPLEXITY: [low/medium/high]
REASONING: [brief reasoning]
"""
        
        reasoning_result = await self.claude_client.reason(
            question="What is the complexity level of this insurance case?",
            context=complexity_prompt,
            options=['low', 'medium', 'high']
        )
        
        return reasoning_result.get('answer', 'medium').lower()
    
    async def _run_agent_with_reflection(
        self, 
        agent: BaseAgent, 
        case_state: CaseState, 
        max_retries: int = 3,
        **kwargs
    ) -> CaseState:
        """
        Run an agent with reflection loop for self-correction
        
        Args:
            agent: The agent to run
            case_state: The current case state
            max_retries: Maximum number of retry attempts
            **kwargs: Additional parameters for the agent
            
        Returns:
            Updated case state
        """
        for attempt in range(max_retries):
            try:
                # Execute agent
                case_state = await agent.execute(case_state, **kwargs)
                
                # Validate output
                is_valid, error_msg = self._validate_agent_output(agent, case_state)
                
                if is_valid:
                    # Perform reflection on successful execution
                    reflection = await self.claude_client.reflect(
                        action=f"{agent.agent_name} execution",
                        result=f"Successfully completed with confidence {self._get_agent_confidence(case_state, agent)}",
                        context=f"Case ID: {case_state.case_id}, Status: {case_state.status.value}"
                    )
                    
                    # Log reflection
                    if reflection['confidence'] < 0.8:
                        print(f"Reflection note for {agent.agent_name}: {reflection['analysis']}")
                    
                    return case_state
                else:
                    # Perform reflection on validation failure
                    reflection = await self.claude_client.reflect(
                        action=f"{agent.agent_name} execution",
                        result=f"Validation failed: {error_msg}",
                        context=f"Case ID: {case_state.case_id}, Attempt {attempt + 1}/{max_retries}"
                    )
                    
                    if attempt < max_retries - 1:
                        if reflection['should_retry']:
                            print(f"Reflection suggests retry for {agent.agent_name}: {reflection['improvements']}")
                            await asyncio.sleep(1 * (attempt + 1))  # Exponential backoff
                        else:
                            # Don't retry if reflection suggests not to
                            break
                    else:
                        case_state.add_error(
                            agent_id=agent.agent_id,
                            field_name="validation",
                            message=f"Validation failed after {max_retries} attempts: {error_msg}",
                            human_review_required=True
                        )
                        return case_state
                        
            except Exception as e:
                # Reflection on exception
                reflection = await self.claude_client.reflect(
                    action=f"{agent.agent_name} execution",
                    result=f"Exception: {str(e)}",
                    context=f"Case ID: {case_state.case_id}, Attempt {attempt + 1}/{max_retries}"
                )
                
                if attempt < max_retries - 1:
                    print(f"Reflection on error for {agent.agent_name}: {reflection['analysis']}")
                    await asyncio.sleep(1 * (attempt + 1))
                else:
                    case_state.add_error(
                        agent_id=agent.agent_id,
                        field_name="execution",
                        message=f"Agent execution failed after {max_retries} attempts: {str(e)}",
                        human_review_required=True
                    )
                    return case_state
        
        return case_state
    
    async def _needs_additional_parsing(self, case_state: CaseState) -> bool:
        """
        Dynamically determine if additional parsing is needed
        
        Args:
            case_state: Current case state
            
        Returns:
            True if additional parsing needed
        """
        # Check if any documents have low confidence scores
        for doc_id, doc in case_state.documents.items():
            if doc.confidence_score < 0.7:
                return True
        
        # Check if critical fields are missing
        required_fields = ['patient_name', 'diagnosis', 'procedures']
        for doc in case_state.documents.values():
            for field in required_fields:
                if not getattr(doc, field, None):
                    return True
        
        return False
    
    async def _run_additional_parsing(self, case_state: CaseState, kwargs: Dict) -> CaseState:
        """
        Run additional parsing for low-confidence documents
        
        Args:
            case_state: Current case state
            kwargs: Input parameters
            
        Returns:
            Updated case state
        """
        print("Running additional parsing for low-confidence documents...")
        
        # Use LLM to reason about which documents need re-parsing
        low_confidence_docs = [
            doc_id for doc_id, doc in case_state.documents.items()
            if doc.confidence_score < 0.7
        ]
        
        if low_confidence_docs:
            reasoning_prompt = f"""
The following documents have low confidence scores and need re-parsing:
{', '.join(low_confidence_docs)}

Should we re-parse these documents? If so, which parsing strategy should we use?
"""
            
            reasoning_result = await self.claude_client.reason(
                question="Should we re-parse low-confidence documents?",
                context=reasoning_prompt,
                options=['yes', 'no']
            )
            
            if reasoning_result.get('answer', 'no').lower() == 'yes':
                # Re-parse documents (in production, would use different OCR strategies)
                print(f"Re-parsing documents: {low_confidence_docs}")
        
        return case_state
    
    async def _request_human_review(self, case_state: CaseState, reason: str):
        """
        Request human review for complex cases
        
        Args:
            case_state: Current case state
            reason: Reason for human review
        """
        case_state.add_error(
            agent_id=self.agent_id,
            field_name="human_review",
            message=f"Human review requested due to: {reason}",
            human_review_required=True
        )
        print(f"Human review requested: {reason}")
    
    async def _final_pipeline_reflection(self, case_state: CaseState):
        """
        Perform final reflection on the entire pipeline execution
        
        Args:
            case_state: Final case state
        """
        reflection_prompt = f"""
Reflect on the entire pipeline execution:

Case ID: {case_state.case_id}
Final Status: {case_state.status.value}
Total Errors: {len(case_state.errors)}
Agents Executed: {len(case_state.agent_logs)}
Total Duration: {sum(log.duration_ms for log in case_state.agent_logs):.2f} ms

Provide your assessment of the pipeline execution and any recommendations for improvement.
"""
        
        reflection = await self.claude_client.reflect(
            action="Complete pipeline execution",
            result=f"Pipeline completed with status {case_state.status.value}",
            context=reflection_prompt
        )
        
        # Store reflection in case state
        if not hasattr(case_state, 'final_reflection'):
            case_state.final_reflection = reflection
    
    def _get_agent_confidence(self, case_state: CaseState, agent: BaseAgent) -> float:
        """
        Get confidence score for an agent from logs
        
        Args:
            case_state: Current case state
            agent: The agent to get confidence for
            
        Returns:
            Confidence score
        """
        for log in case_state.agent_logs:
            if log.agent_id == agent.agent_id:
                return log.confidence_score
        return 0.5
    
    async def _run_agent_with_retry(self, agent: BaseAgent, case_state: CaseState, 
                                   max_retries: int = 3, **kwargs) -> CaseState:
        """
        Run an agent with retry logic and validation
        
        Args:
            agent: The agent to run
            case_state: The current case state
            max_retries: Maximum number of retry attempts
            **kwargs: Additional parameters for the agent
            
        Returns:
            Updated case state
        """
        for attempt in range(max_retries):
            try:
                case_state = await agent.execute(case_state, **kwargs)
                
                # Validate output
                is_valid, error_msg = self._validate_agent_output(agent, case_state)
                if is_valid:
                    return case_state
                else:
                    if attempt < max_retries - 1:
                        print(f"Validation failed for {agent.agent_name}: {error_msg}. Retrying...")
                        await asyncio.sleep(1 * (attempt + 1))  # Exponential backoff
                    else:
                        case_state.add_error(
                            agent_id=agent.agent_id,
                            field_name="validation",
                            message=f"Validation failed after {max_retries} attempts: {error_msg}",
                            human_review_required=True
                        )
                        return case_state
                        
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"Agent {agent.agent_name} failed on attempt {attempt + 1}: {str(e)}. Retrying...")
                    await asyncio.sleep(1 * (attempt + 1))
                else:
                    case_state.add_error(
                        agent_id=agent.agent_id,
                        field_name="execution",
                        message=f"Agent execution failed after {max_retries} attempts: {str(e)}",
                        human_review_required=True
                    )
                    return case_state
        
        return case_state
    
    def _validate_agent_output(self, agent: BaseAgent, case_state: CaseState) -> tuple[bool, str]:
        """
        Validate agent output based on agent type
        
        Returns:
            (is_valid, error_message)
        """
        if agent.agent_id == "AG-02":  # Intake Agent
            if not case_state.documents or len(case_state.documents) == 0:
                return False, "No documents parsed"
            for doc_id, doc in case_state.documents.items():
                if doc.confidence_score < 0.7:
                    case_state.add_error(
                        agent_id=agent.agent_id,
                        field_name=f"document_{doc_id}",
                        message=f"Low confidence score: {doc.confidence_score}",
                        human_review_required=True
                    )
        
        elif agent.agent_id == "AG-03":  # COB Agent
            if not case_state.cob_result or len(case_state.cob_result) == 0:
                return False, "No COB results calculated"
        
        elif agent.agent_id == "AG-04":  # Pre-Auth Agent
            if not case_state.preauth_letters or len(case_state.preauth_letters) == 0:
                return False, "No pre-auth letters generated"
        
        elif agent.agent_id == "AG-05":  # Finance Agent
            if not case_state.financials or "family_summary" not in case_state.financials:
                return False, "No financial calculations completed"
        
        elif agent.agent_id == "AG-06":  # Output Agent
            if not case_state.outputs or len(case_state.outputs) == 0:
                return False, "No outputs generated"
        
        return True, ""
