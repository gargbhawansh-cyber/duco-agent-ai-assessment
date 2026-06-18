"""
Shared State Management for DuCO-Agent
Maintains case_state object shared across all agents
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum


class CaseStatus(Enum):
    INTAKE = "INTAKE"
    COB = "COB"
    FINANCE = "FINANCE"
    PREAUTH = "PREAUTH"
    OUTPUT = "OUTPUT"
    DONE = "DONE"
    ERROR = "ERROR"


@dataclass
class PatientRecord:
    name: str
    dob: Optional[str] = None
    policy_numbers: Dict[str, str] = field(default_factory=dict)
    role_in_plans: Dict[str, str] = field(default_factory=dict)  # plan_id -> "PRIMARY" or "DEPENDENT"


@dataclass
class ParsedDoc:
    document_type: str
    patient_name: str
    date_of_service: Optional[str] = None
    provider_name: Optional[str] = None
    diagnosis: Optional[str] = None
    icd10_codes: List[str] = field(default_factory=list)
    procedures: List[Dict[str, Any]] = field(default_factory=list)  # {cpt_code, description, amount_inr}
    total_billed_inr: Optional[float] = None
    handwritten_notes: str = ""
    confidence_score: float = 0.0
    extraction_notes: str = ""
    raw_text: str = ""


@dataclass
class COBResult:
    primary_plan: str
    secondary_plan: str
    billed: float
    deductible_applied: float
    plan_primary_payment: float
    plan_secondary_payment: float
    patient_oop: float
    audit_steps: List[str] = field(default_factory=list)


@dataclass
class FinancialResult:
    billed_inr: float
    plan_primary_deductible: float
    plan_primary_covered: float
    plan_primary_pays: float
    patient_to_plan_primary: float
    residual_to_plan_secondary: float
    plan_secondary_pays: float
    patient_final_oop: float
    oop_max_check: Dict[str, bool] = field(default_factory=dict)
    step_by_step: List[str] = field(default_factory=list)


@dataclass
class AgentLog:
    agent_id: str
    agent_name: str
    timestamp: datetime
    input_summary: str
    output_summary: str
    duration_ms: float
    confidence_score: float = 1.0


@dataclass
class Error:
    agent_id: str
    field_name: str
    message: str
    human_review_required: bool = False
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class CaseState:
    """Central state object shared across all DuCO-Agent agents"""
    
    case_id: str
    status: CaseStatus = CaseStatus.INTAKE
    created_at: datetime = field(default_factory=datetime.now)
    
    # Patient information
    patients: Dict[str, PatientRecord] = field(default_factory=dict)
    
    # Parsed documents
    documents: Dict[str, ParsedDoc] = field(default_factory=dict)
    
    # COB results
    cob_result: Dict[str, COBResult] = field(default_factory=dict)
    
    # Financial calculations
    financials: Dict[str, Any] = field(default_factory=dict)
    
    # Pre-auth letters
    preauth_letters: Dict[str, str] = field(default_factory=dict)
    
    # Outputs
    outputs: Dict[str, Any] = field(default_factory=dict)
    
    # Agent logs
    agent_logs: List[AgentLog] = field(default_factory=list)
    
    # Errors
    errors: List[Error] = field(default_factory=list)
    
    # Plan parameters (mock for assessment)
    plan_parameters: Dict[str, Dict[str, Any]] = field(default_factory=lambda: {
        "plan_a": {
            "insurer": "Insurer1",
            "deductible_inr": 10000,
            "coinsurance_patient_percent": 20,
            "oop_max_inr": 100000,
            "network_status": "in-network"
        },
        "plan_b": {
            "insurer": "Insurer2",
            "deductible_inr": 15000,
            "coinsurance_patient_percent": 20,
            "oop_max_inr": 120000,
            "network_status": "in-network"
        }
    })
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert case_state to dictionary for serialization"""
        return {
            "case_id": self.case_id,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "patients": {k: {
                "name": v.name,
                "dob": v.dob,
                "policy_numbers": v.policy_numbers,
                "role_in_plans": v.role_in_plans
            } for k, v in self.patients.items()},
            "documents": {k: {
                "document_type": v.document_type,
                "patient_name": v.patient_name,
                "date_of_service": v.date_of_service,
                "provider_name": v.provider_name,
                "diagnosis": v.diagnosis,
                "icd10_codes": v.icd10_codes,
                "procedures": v.procedures,
                "total_billed_inr": v.total_billed_inr,
                "handwritten_notes": v.handwritten_notes,
                "confidence_score": v.confidence_score,
                "extraction_notes": v.extraction_notes,
                "raw_text": v.raw_text
            } for k, v in self.documents.items()},
            "cob_result": {k: {
                "primary_plan": v.primary_plan,
                "secondary_plan": v.secondary_plan,
                "billed": v.billed,
                "deductible_applied": v.deductible_applied,
                "plan_primary_payment": v.plan_primary_payment,
                "plan_secondary_payment": v.plan_secondary_payment,
                "patient_oop": v.patient_oop,
                "audit_steps": v.audit_steps
            } for k, v in self.cob_result.items()},
            "financials": self.financials,
            "preauth_letters": self.preauth_letters,
            "outputs": self.outputs,
            "agent_logs": [{
                "agent_id": log.agent_id,
                "agent_name": log.agent_name,
                "timestamp": log.timestamp.isoformat(),
                "input_summary": log.input_summary,
                "output_summary": log.output_summary,
                "duration_ms": log.duration_ms,
                "confidence_score": log.confidence_score
            } for log in self.agent_logs],
            "errors": [{
                "agent_id": err.agent_id,
                "field_name": err.field_name,
                "message": err.message,
                "human_review_required": err.human_review_required,
                "timestamp": err.timestamp.isoformat()
            } for err in self.errors],
            "plan_parameters": self.plan_parameters
        }
    
    def add_agent_log(self, agent_id: str, agent_name: str, input_summary: str, 
                      output_summary: str, duration_ms: float, confidence_score: float = 1.0):
        """Add an agent execution log"""
        log = AgentLog(
            agent_id=agent_id,
            agent_name=agent_name,
            timestamp=datetime.now(),
            input_summary=input_summary,
            output_summary=output_summary,
            duration_ms=duration_ms,
            confidence_score=confidence_score
        )
        self.agent_logs.append(log)
    
    def add_error(self, agent_id: str, field_name: str, message: str, 
                  human_review_required: bool = False):
        """Add an error to the case state"""
        error = Error(
            agent_id=agent_id,
            field_name=field_name,
            message=message,
            human_review_required=human_review_required
        )
        self.errors.append(error)
    
    def update_status(self, new_status: CaseStatus):
        """Update the case status"""
        self.status = new_status
