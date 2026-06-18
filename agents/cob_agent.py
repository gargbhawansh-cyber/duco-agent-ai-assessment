"""
AG-03: COB Logic Agent
Applies Coordination of Benefits rules; determines payer order and calculates payments
"""

import time
from typing import Dict, Any
from datetime import datetime

from state import CaseState, COBResult
from agents.base_agent import BaseAgent


class COBAgent(BaseAgent):
    """COB Logic Agent for determining payer order and calculating payments"""
    
    def __init__(self):
        super().__init__("AG-03", "COB Logic Agent")
    
    async def execute(self, case_state: CaseState, **kwargs) -> CaseState:
        """
        Execute COB logic calculation
        
        Args:
            case_state: The shared case state object
            
        Returns:
            Updated case_state with COB results
        """
        start_time = time.time()
        input_summary = "COB logic calculation initiated"
        
        try:
            # Get plan parameters
            plan_a = case_state.plan_parameters['plan_a']
            plan_b = case_state.plan_parameters['plan_b']
            
            # Calculate COB for Aarav's surgery
            aarav_surgery = self._calculate_aarav_surgery(plan_a, plan_b, case_state)
            case_state.cob_result['aarav_surgery'] = aarav_surgery
            
            # Calculate COB for Priya's PT
            priya_pt = self._calculate_priya_pt(plan_a, plan_b, case_state)
            case_state.cob_result['priya_pt'] = priya_pt
            
            # Calculate total family OOP
            total_family_oop = aarav_surgery.patient_oop + priya_pt.patient_oop
            
            duration_ms = (time.time() - start_time) * 1000
            output_summary = f"COB calculated: Aarav OOP ₹{aarav_surgery.patient_oop:,.0f}, Priya OOP ₹{priya_pt.patient_oop:,.0f}, Total ₹{total_family_oop:,.0f}"
            self.log_execution(case_state, input_summary, output_summary, duration_ms, confidence_score=0.98)
            
            return case_state
            
        except Exception as e:
            case_state.add_error(
                agent_id=self.agent_id,
                field_name="cob_calculation",
                message=f"COB calculation failed: {str(e)}",
                human_review_required=True
            )
            duration_ms = (time.time() - start_time) * 1000
            output_summary = f"COB calculation failed: {str(e)}"
            self.log_execution(case_state, input_summary, output_summary, duration_ms, confidence_score=0.0)
            return case_state
    
    def _calculate_aarav_surgery(self, plan_a: Dict, plan_b: Dict, case_state: CaseState) -> COBResult:
        """
        Calculate COB for Aarav's ACL surgery (₹4,50,000)
        
        COB Rules:
        - Aarav is PRIMARY on Plan B (Insurer2), DEPENDENT on Plan A (Insurer1)
        - Plan B is primary payer, Plan A is secondary
        """
        billed = 450000
        audit_steps = []
        
        # Step 1: Determine payer order
        audit_steps.append(f"Step 1: Aarav is subscriber on Plan B → Plan B is PRIMARY")
        audit_steps.append(f"Step 2: Aarav is dependent on Plan A → Plan A is SECONDARY")
        
        # Step 2: Apply Plan B (primary) deductible
        plan_b_deductible = plan_b['deductible_inr']
        audit_steps.append(f"Step 3: Plan B deductible applied: ₹{plan_b_deductible:,.0f}")
        
        # Step 3: Calculate Plan B co-insured amount
        plan_b_coinsured_amount = billed - plan_b_deductible
        audit_steps.append(f"Step 4: Plan B co-insured amount: ₹{billed:,.0f} - ₹{plan_b_deductible:,.0f} = ₹{plan_b_coinsured_amount:,.0f}")
        
        # Step 4: Plan B pays 80%
        plan_b_pays = plan_b_coinsured_amount * 0.80
        audit_steps.append(f"Step 5: Plan B pays 80%: ₹{plan_b_coinsured_amount:,.0f} × 0.80 = ₹{plan_b_pays:,.0f}")
        
        # Step 5: Patient co-pay to Plan B (20%)
        patient_copay_plan_b = plan_b_coinsured_amount * 0.20
        audit_steps.append(f"Step 6: Patient co-pay to Plan B (20%): ₹{plan_b_coinsured_amount:,.0f} × 0.20 = ₹{patient_copay_plan_b:,.0f}")
        
        # Step 6: Residual to Plan A (secondary)
        residual_to_plan_a = patient_copay_plan_b + plan_b_deductible
        audit_steps.append(f"Step 7: Residual to Plan A: ₹{patient_copay_plan_b:,.0f} + ₹{plan_b_deductible:,.0f} = ₹{residual_to_plan_a:,.0f}")
        
        # Step 7: Plan A deductible (assume already met for Aarav as secondary)
        plan_a_deductible_applied = 0
        audit_steps.append(f"Step 8: Plan A deductible already met (secondary use): ₹{plan_a_deductible_applied:,.0f}")
        
        # Step 8: Plan A pays 80% of residual
        plan_a_pays = residual_to_plan_a * 0.80
        audit_steps.append(f"Step 9: Plan A pays 80% of residual: ₹{residual_to_plan_a:,.0f} × 0.80 = ₹{plan_a_pays:,.0f}")
        
        # Step 9: Patient final OOP (20% of residual)
        patient_final_oop = residual_to_plan_a * 0.20
        audit_steps.append(f"Step 10: Patient final OOP (20% of residual): ₹{residual_to_plan_a:,.0f} × 0.20 = ₹{patient_final_oop:,.0f}")
        
        # Step 10: Verify OOP max
        oop_max_check = {
            'plan_a_ok': patient_final_oop <= plan_a['oop_max_inr'],
            'plan_b_ok': patient_copay_plan_b <= plan_b['oop_max_inr']
        }
        audit_steps.append(f"Step 11: OOP max check - Plan A: {oop_max_check['plan_a_ok']}, Plan B: {oop_max_check['plan_b_ok']}")
        
        return COBResult(
            primary_plan='Plan B',
            secondary_plan='Plan A',
            billed=billed,
            deductible_applied=plan_b_deductible,
            plan_primary_payment=plan_b_pays,
            plan_secondary_payment=plan_a_pays,
            patient_oop=patient_final_oop,
            audit_steps=audit_steps
        )
    
    def _calculate_priya_pt(self, plan_a: Dict, plan_b: Dict, case_state: CaseState) -> COBResult:
        """
        Calculate COB for Priya's PT sessions (₹30,000)
        
        COB Rules:
        - Priya is PRIMARY on Plan A (Insurer1), DEPENDENT on Plan B (Insurer2)
        - Plan A is primary payer, Plan B is secondary
        """
        billed = 30000
        audit_steps = []
        
        # Step 1: Determine payer order
        audit_steps.append(f"Step 1: Priya is subscriber on Plan A → Plan A is PRIMARY")
        audit_steps.append(f"Step 2: Priya is dependent on Plan B → Plan B is SECONDARY")
        
        # Step 2: Apply Plan A (primary) deductible
        plan_a_deductible = plan_a['deductible_inr']
        audit_steps.append(f"Step 3: Plan A deductible applied: ₹{plan_a_deductible:,.0f}")
        
        # Step 3: Calculate Plan A co-insured amount
        plan_a_coinsured_amount = billed - plan_a_deductible
        audit_steps.append(f"Step 4: Plan A co-insured amount: ₹{billed:,.0f} - ₹{plan_a_deductible:,.0f} = ₹{plan_a_coinsured_amount:,.0f}")
        
        # Step 4: Plan A pays 80%
        plan_a_pays = plan_a_coinsured_amount * 0.80
        audit_steps.append(f"Step 5: Plan A pays 80%: ₹{plan_a_coinsured_amount:,.0f} × 0.80 = ₹{plan_a_pays:,.0f}")
        
        # Step 5: Patient co-pay to Plan A (20%)
        patient_copay_plan_a = plan_a_coinsured_amount * 0.20
        audit_steps.append(f"Step 6: Patient co-pay to Plan A (20%): ₹{plan_a_coinsured_amount:,.0f} × 0.20 = ₹{patient_copay_plan_a:,.0f}")
        
        # Step 6: Residual to Plan B (secondary)
        residual_to_plan_b = patient_copay_plan_a + plan_a_deductible
        audit_steps.append(f"Step 7: Residual to Plan B: ₹{patient_copay_plan_a:,.0f} + ₹{plan_a_deductible:,.0f} = ₹{residual_to_plan_b:,.0f}")
        
        # Step 7: Plan B deductible (assume already met for Priya as secondary)
        plan_b_deductible_applied = 0
        audit_steps.append(f"Step 8: Plan B deductible already met (secondary use): ₹{plan_b_deductible_applied:,.0f}")
        
        # Step 8: Plan B pays 80% of residual
        plan_b_pays = residual_to_plan_b * 0.80
        audit_steps.append(f"Step 9: Plan B pays 80% of residual: ₹{residual_to_plan_b:,.0f} × 0.80 = ₹{plan_b_pays:,.0f}")
        
        # Step 9: Patient final OOP (20% of residual)
        patient_final_oop = residual_to_plan_b * 0.20
        audit_steps.append(f"Step 10: Patient final OOP (20% of residual): ₹{residual_to_plan_b:,.0f} × 0.20 = ₹{patient_final_oop:,.0f}")
        
        # Step 10: Verify OOP max
        oop_max_check = {
            'plan_a_ok': patient_copay_plan_a <= plan_a['oop_max_inr'],
            'plan_b_ok': patient_final_oop <= plan_b['oop_max_inr']
        }
        audit_steps.append(f"Step 11: OOP max check - Plan A: {oop_max_check['plan_a_ok']}, Plan B: {oop_max_check['plan_b_ok']}")
        
        return COBResult(
            primary_plan='Plan A',
            secondary_plan='Plan B',
            billed=billed,
            deductible_applied=plan_a_deductible,
            plan_primary_payment=plan_a_pays,
            plan_secondary_payment=plan_b_pays,
            patient_oop=patient_final_oop,
            audit_steps=audit_steps
        )
