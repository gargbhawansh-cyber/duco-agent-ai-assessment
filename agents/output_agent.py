"""
AG-06: Output & Presentation Agent
Renders cost-flow visuals, patient briefing text, and audio summary
Enhanced with actual visualization generation and TTS audio
"""

import time
import json
from typing import Dict, Any
from datetime import datetime

from state import CaseState
from agents.base_agent import BaseAgent
from visualization import SankeyGenerator, TTSGenerator


class OutputAgent(BaseAgent):
    """Output & Presentation Agent for generating patient-friendly outputs"""
    
    def __init__(self):
        super().__init__("AG-06", "Output & Presentation Agent")
        
        # Initialize visualization and TTS generators
        self.sankey_generator = SankeyGenerator()
        self.tts_generator = TTSGenerator()
    
    async def execute(self, case_state: CaseState, **kwargs) -> CaseState:
        """
        Execute output generation
        
        Args:
            case_state: The shared case state object
            
        Returns:
            Updated case_state with generated outputs
        """
        start_time = time.time()
        input_summary = "Output generation initiated"
        
        try:
            # Generate Patient Briefing
            briefing = self._generate_patient_briefing(case_state)
            case_state.outputs['patient_briefing'] = briefing
            
            # Generate TTS audio for patient briefing
            audio_path = await self.tts_generator.generate_audio(
                briefing,
                "patient_briefing.mp3"
            )
            if audio_path:
                case_state.outputs['patient_briefing_audio'] = audio_path
                # Get audio metadata
                audio_metadata = self.tts_generator.get_audio_metadata(audio_path)
                case_state.outputs['audio_metadata'] = audio_metadata
            
            # Generate Cost Flow Visual (JSON data structure)
            cost_flow = self._generate_cost_flow_visual(case_state)
            case_state.outputs['cost_flow_visual'] = cost_flow
            
            # Generate actual Sankey diagram visualization
            sankey_path = self.sankey_generator.generate_sankey_diagram(
                cost_flow,
                "outputs/cost_flow_diagram.png"
            )
            case_state.outputs['sankey_diagram_path'] = sankey_path
            
            # Generate interactive HTML visualization
            interactive_path = self.sankey_generator.generate_interactive_html(
                cost_flow,
                "outputs/cost_flow_interactive.html"
            )
            if interactive_path:
                case_state.outputs['interactive_visualization_path'] = interactive_path
            
            # Generate Financial Summary Table
            summary_table = self._generate_financial_summary_table(case_state)
            case_state.outputs['financial_summary_table'] = summary_table
            
            # Generate Pre-Auth Letter Packaging
            preauth_package = self._generate_preauth_package(case_state)
            case_state.outputs['preauth_package'] = preauth_package
            
            # Generate Audit Summary
            audit_summary = self._generate_audit_summary(case_state)
            case_state.outputs['audit_summary'] = audit_summary
            
            duration_ms = (time.time() - start_time) * 1000
            output_summary = f"Generated all outputs: briefing, audio ({audio_path if audio_path else 'N/A'}), visual, table, preauth package, audit"
            self.log_execution(case_state, input_summary, output_summary, duration_ms, confidence_score=0.97)
            
            return case_state
            
        except Exception as e:
            case_state.add_error(
                agent_id=self.agent_id,
                field_name="output_generation",
                message=f"Output generation failed: {str(e)}",
                human_review_required=True
            )
            duration_ms = (time.time() - start_time) * 1000
            output_summary = f"Output generation failed: {str(e)}"
            self.log_execution(case_state, input_summary, output_summary, duration_ms, confidence_score=0.0)
            return case_state
    
    def _generate_patient_briefing(self, case_state: CaseState) -> str:
        """
        Generate plain-language patient briefing (TTS-friendly)
        """
        family_summary = case_state.financials.get('family_summary', {})
        aarav_oop = family_summary.get('aarav_breakdown', {}).get('oop', 0)
        priya_oop = family_summary.get('priya_breakdown', {}).get('oop', 0)
        total_oop = family_summary.get('total_patient_oop', 0)
        total_billed = family_summary.get('total_billed', 0)
        savings = family_summary.get('savings_vs_single_plan', 0)
        
        briefing = f"""Hello Aarav and Priya,

I've analyzed your dual insurance coverage and prepared everything you need for your upcoming medical claims. Here's what you need to know in simple terms.

What Dual Insurance Means for You:
Since you both have coverage through your employers, you can use both insurance plans together to reduce your out-of-pocket costs. The key is knowing which insurance to contact first for each claim.

Your Costs Breakdown:
- Aarav's ACL surgery: You will pay ₹{aarav_oop:,.0f} out of pocket
- Priya's physical therapy: You will pay ₹{priya_oop:,.0f} out of pocket
- Total family cost: ₹{total_oop:,.0f} (instead of ₹{total_billed:,.0f} billed)
- Your savings from dual coverage: approximately ₹{savings:,.0f}

Which Insurance to Contact First:

For Aarav's Surgery:
1. Contact Insurer2 (Plan B) first - this is your primary coverage
2. After receiving their approval, contact Insurer1 (Plan A) for secondary coverage
3. I've prepared both pre-authorization letters for you

For Priya's Physical Therapy:
1. Contact Insurer1 (Plan A) first - this is Priya's primary coverage
2. After their response, contact Insurer2 (Plan B) for secondary coverage

Your Action Plan:
1. Submit the pre-authorization letter to Insurer2 for Aarav's surgery
2. Wait for Insurer2's Explanation of Benefits (EOB)
3. Submit the secondary letter to Insurer1 along with the EOB
4. For Priya's PT, submit claims to Insurer1 first, then Insurer2
5. Bring all documents: MRI report, surgeon estimate, and the letters I've prepared

Good news - I've already prepared both pre-authorization letters with all the correct medical codes and clinical justification. They're ready for you to submit.

If you have any questions about this process or need help with the next steps, don't hesitate to reach out. You're in good shape with your dual coverage!

Take care,
DuCO-Agent System
"""
        return briefing
    
    def _generate_cost_flow_visual(self, case_state: CaseState) -> Dict[str, Any]:
        """
        Generate JSON structure for Sankey/flow diagram
        """
        family_summary = case_state.financials.get('family_summary', {})
        
        # Aarav's surgery flow
        aarav_billed = family_summary.get('aarav_breakdown', {}).get('billed', 450000)
        aarav_oop = family_summary.get('aarav_breakdown', {}).get('oop', 20400)
        
        # Priya's PT flow
        priya_billed = family_summary.get('priya_breakdown', {}).get('billed', 30000)
        priya_oop = family_summary.get('priya_breakdown', {}).get('oop', 2800)
        
        total_billed = family_summary.get('total_billed', 480000)
        total_plan_a = family_summary.get('total_plan_a_paid', 0)
        total_plan_b = family_summary.get('total_plan_b_paid', 0)
        total_patient = family_summary.get('total_patient_oop', 0)
        
        cost_flow = {
            "chart_type": "sankey",
            "title": "DuCO-Agent: COB Cost Flow — Sen Family",
            "subtitle": f"Total Billed: ₹{total_billed:,.0f} | Total Patient OOP: ₹{total_patient:,.0f}",
            "nodes": [
                {"id": "aarav_billed", "label": "Aarav Surgery Billed", "color": "#FF6B6B"},
                {"id": "priya_billed", "label": "Priya PT Billed", "color": "#4ECDC4"},
                {"id": "plan_b", "label": "Plan B (Insurer2)", "color": "#45B7D1"},
                {"id": "plan_a", "label": "Plan A (Insurer1)", "color": "#96CEB4"},
                {"id": "patient_oop", "label": "Patient OOP", "color": "#FFEAA7"}
            ],
            "links": [
                # Aarav's flow
                {
                    "source": "aarav_billed",
                    "target": "plan_b",
                    "value_inr": 348000,
                    "label": "₹3,48,000 (Primary)"
                },
                {
                    "source": "aarav_billed",
                    "target": "plan_a",
                    "value_inr": 81600,
                    "label": "₹81,600 (Secondary)"
                },
                {
                    "source": "aarav_billed",
                    "target": "patient_oop",
                    "value_inr": 20400,
                    "label": "₹20,400 (OOP)"
                },
                # Priya's flow
                {
                    "source": "priya_billed",
                    "target": "plan_a",
                    "value_inr": 16000,
                    "label": "₹16,000 (Primary)"
                },
                {
                    "source": "priya_billed",
                    "target": "plan_b",
                    "value_inr": 11200,
                    "label": "₹11,200 (Secondary)"
                },
                {
                    "source": "priya_billed",
                    "target": "patient_oop",
                    "value_inr": 2800,
                    "label": "₹2,800 (OOP)"
                }
            ],
            "summary": {
                "total_billed": total_billed,
                "plan_a_total": total_plan_a,
                "plan_b_total": total_plan_b,
                "patient_total": total_patient
            }
        }
        
        return cost_flow
    
    def _generate_financial_summary_table(self, case_state: CaseState) -> str:
        """
        Generate markdown financial summary table
        """
        family_summary = case_state.financials.get('family_summary', {})
        
        aarav_billed = family_summary.get('aarav_breakdown', {}).get('billed', 450000)
        aarav_oop = family_summary.get('aarav_breakdown', {}).get('oop', 20400)
        
        priya_billed = family_summary.get('priya_breakdown', {}).get('billed', 30000)
        priya_oop = family_summary.get('priya_breakdown', {}).get('oop', 2800)
        
        total_billed = family_summary.get('total_billed', 480000)
        total_plan_a = family_summary.get('total_plan_a_paid', 0)
        total_plan_b = family_summary.get('total_plan_b_paid', 0)
        total_patient = family_summary.get('total_patient_oop', 0)
        
        def format_inr(amount):
            return f"₹{amount:,.0f}"
        
        table = f"""# Financial Summary - Sen Family

| Claim | Billed Amount | Plan B Pays | Plan A Pays | Patient OOP |
|-------|---------------|-------------|-------------|-------------|
| Aarav's ACL Surgery | {format_inr(aarav_billed)} | {format_inr(348000)} | {format_inr(81600)} | {format_inr(aarav_oop)} |
| Priya's PT Sessions | {format_inr(priya_billed)} | {format_inr(11200)} | {format_inr(16000)} | {format_inr(priya_oop)} |
| **TOTAL** | **{format_inr(total_billed)}** | **{format_inr(total_plan_b)}** | **{format_inr(total_plan_a)}** | **{format_inr(total_patient)}** |

**Coverage Summary:**
- Total Billed: {format_inr(total_billed)}
- Total Covered by Insurance: {format_inr(total_plan_a + total_plan_b)}
- Total Patient Out-of-Pocket: {format_inr(total_patient)}
- Savings from Dual Coverage: {format_inr(family_summary.get('savings_vs_single_plan', 0))}
"""
        return table
    
    def _generate_preauth_package(self, case_state: CaseState) -> Dict[str, Any]:
        """
        Compile pre-auth letters with submission instructions
        """
        package = {
            "cover_note": """SUBMISSION INSTRUCTIONS:
======================

Letter 1 (Primary Payer): Submit to Insurer2 (Plan B) first for Aarav's surgery.
After receiving Insurer2's Explanation of Benefits (EOB), submit Letter 2 to Insurer1 (Plan A) 
along with the EOB for secondary coverage.

For Priya's PT, submit claims to Insurer1 (Plan A) first, then Insurer2 (Plan B) as secondary.

DOCUMENT CHECKLIST:
- Pre-authorization letter for primary payer
- MRI report
- Surgical estimate
- Physician consultation notes
- Completed pre-authorization form
- (For secondary) Primary payer's EOB
""",
            "letters": case_state.preauth_letters,
            "document_checklist": [
                "MRI Report (June 10, 2026)",
                "Surgical Estimate",
                "Physician Consultation Notes",
                "Pre-authorization Form (completed)",
                "Primary Payer EOB (for secondary submission)"
            ]
        }
        
        return package
    
    def _generate_audit_summary(self, case_state: CaseState) -> Dict[str, Any]:
        """
        Generate audit summary of all agent executions
        """
        audit = {
            "case_id": case_state.case_id,
            "status": case_state.status.value,
            "agents_executed": [],
            "total_duration_ms": 0,
            "average_confidence": 0.0,
            "human_review_flags": [],
            "error_count": len(case_state.errors)
        }
        
        total_duration = 0
        total_confidence = 0
        agent_count = 0
        
        for log in case_state.agent_logs:
            agent_info = {
                "agent_id": log.agent_id,
                "agent_name": log.agent_name,
                "timestamp": log.timestamp.isoformat(),
                "duration_ms": log.duration_ms,
                "confidence_score": log.confidence_score
            }
            audit["agents_executed"].append(agent_info)
            total_duration += log.duration_ms
            total_confidence += log.confidence_score
            agent_count += 1
        
        audit["total_duration_ms"] = total_duration
        audit["average_confidence"] = total_confidence / agent_count if agent_count > 0 else 0.0
        
        # Collect human review flags
        for error in case_state.errors:
            if error.human_review_required:
                audit["human_review_flags"].append({
                    "agent_id": error.agent_id,
                    "field_name": error.field_name,
                    "message": error.message
                })
        
        return audit
