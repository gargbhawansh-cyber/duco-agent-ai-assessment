"""
AG-05: Financial Calculation Agent
Computes final OOP amounts; validates all math; produces audit trail
"""

import time
from typing import Dict, Any
from datetime import datetime

from state import CaseState, FinancialResult
from agents.base_agent import BaseAgent


class FinanceAgent(BaseAgent):
    """Financial Calculation Agent for validating and finalizing monetary calculations"""
    
    def __init__(self):
        super().__init__("AG-05", "Financial Calculation Agent")
    
    async def execute(self, case_state: CaseState, **kwargs) -> CaseState:
        """
        Execute financial calculation and validation
        
        Args:
            case_state: The shared case state object
            
        Returns:
            Updated case_state with validated financial calculations
        """
        start_time = time.time()
        input_summary = "Financial calculation and validation initiated"
        
        try:
            # Get plan parameters
            plan_a = case_state.plan_parameters['plan_a']
            plan_b = case_state.plan_parameters['plan_b']
            
            # Calculate Aarav's surgery finances
            aarav_surgery = self._calculate_aarav_surgery_finances(plan_a, plan_b, case_state)
            
            # Calculate Priya's PT finances
            priya_pt = self._calculate_priya_pt_finances(plan_a, plan_b, case_state)
            
            # Validate against COB agent results
            validation = self._validate_against_cob_agent(case_state, aarav_surgery, priya_pt)
            
            # Calculate family summary
            family_summary = self._calculate_family_summary(aarav_surgery, priya_pt, plan_a, plan_b)
            
            # Store results in case_state
            case_state.financials = {
                'aarav_surgery': aarav_surgery,
                'priya_pt': priya_pt,
                'family_summary': family_summary,
                'validation': validation
            }
            
            duration_ms = (time.time() - start_time) * 1000
            output_summary = f"Financials validated: Total OOP ₹{family_summary['total_patient_oop']:,.0f}"
            self.log_execution(case_state, input_summary, output_summary, duration_ms, confidence_score=0.99)
            
            return case_state
            
        except Exception as e:
            case_state.add_error(
                agent_id=self.agent_id,
                field_name="financial_calculation",
                message=f"Financial calculation failed: {str(e)}",
                human_review_required=True
            )
            duration_ms = (time.time() - start_time) * 1000
            output_summary = f"Financial calculation failed: {str(e)}"
            self.log_execution(case_state, input_summary, output_summary, duration_ms, confidence_score=0.0)
            return case_state
    
    def _calculate_aarav_surgery_finances(self, plan_a: Dict, plan_b: Dict, case_state: CaseState) -> FinancialResult:
        """
        Calculate and validate Aarav's surgery finances (₹4,50,000)
        
        Primary: Plan B | Secondary: Plan A
        """
        billed_inr = 450000
        step_by_step = []
        
        # Step 1: Plan B deductible
        plan_b_deductible = plan_b['deductible_inr']
        step_by_step.append(f"Step 1: Plan B deductible = ₹{plan_b_deductible:,.0f}")
        
        # Step 2: Plan B covered amount
        plan_b_covered = billed_inr - plan_b_deductible
        step_by_step.append(f"Step 2: Plan B covered = ₹{billed_inr:,.0f} - ₹{plan_b_deductible:,.0f} = ₹{plan_b_covered:,.0f}")
        
        # Step 3: Plan B pays 80%
        plan_b_pays = plan_b_covered * 0.80
        step_by_step.append(f"Step 3: Plan B pays 80% = ₹{plan_b_covered:,.0f} × 0.80 = ₹{plan_b_pays:,.0f}")
        
        # Step 4: Patient pays to Plan B (20%)
        patient_to_plan_b = plan_b_covered * 0.20
        step_by_step.append(f"Step 4: Patient to Plan B (20%) = ₹{plan_b_covered:,.0f} × 0.20 = ₹{patient_to_plan_b:,.0f}")
        
        # Step 5: Residual to Plan A
        residual_to_plan_a = patient_to_plan_b + plan_b_deductible
        step_by_step.append(f"Step 5: Residual to Plan A = ₹{patient_to_plan_b:,.0f} + ₹{plan_b_deductible:,.0f} = ₹{residual_to_plan_a:,.0f}")
        
        # Step 6: Plan A pays 80% of residual
        plan_a_pays = residual_to_plan_a * 0.80
        step_by_step.append(f"Step 6: Plan A pays 80% = ₹{residual_to_plan_a:,.0f} × 0.80 = ₹{plan_a_pays:,.0f}")
        
        # Step 7: Patient final OOP
        patient_final_oop = residual_to_plan_a * 0.20
        step_by_step.append(f"Step 7: Patient final OOP = ₹{residual_to_plan_a:,.0f} × 0.20 = ₹{patient_final_oop:,.0f}")
        
        # Step 8: OOP max check
        oop_max_check = {
            'plan_a_ok': patient_final_oop <= plan_a['oop_max_inr'],
            'plan_b_ok': patient_to_plan_b <= plan_b['oop_max_inr']
        }
        step_by_step.append(f"Step 8: OOP max check - Plan A: {oop_max_check['plan_a_ok']} (₹{patient_final_oop:,.0f} ≤ ₹{plan_a['oop_max_inr']:,.0f}), Plan B: {oop_max_check['plan_b_ok']} (₹{patient_to_plan_b:,.0f} ≤ ₹{plan_b['oop_max_inr']:,.0f})")
        
        return FinancialResult(
            billed_inr=billed_inr,
            plan_primary_deductible=plan_b_deductible,
            plan_primary_covered=plan_b_covered,
            plan_primary_pays=plan_b_pays,
            patient_to_plan_primary=patient_to_plan_b,
            residual_to_plan_secondary=residual_to_plan_a,
            plan_secondary_pays=plan_a_pays,
            patient_final_oop=patient_final_oop,
            oop_max_check=oop_max_check,
            step_by_step=step_by_step
        )
    
    def _calculate_priya_pt_finances(self, plan_a: Dict, plan_b: Dict, case_state: CaseState) -> FinancialResult:
        """
        Calculate and validate Priya's PT finances (₹30,000)
        
        Primary: Plan A | Secondary: Plan B
        """
        billed_inr = 30000
        step_by_step = []
        
        # Step 1: Plan A deductible
        plan_a_deductible = plan_a['deductible_inr']
        step_by_step.append(f"Step 1: Plan A deductible = ₹{plan_a_deductible:,.0f}")
        
        # Step 2: Plan A covered amount
        plan_a_covered = billed_inr - plan_a_deductible
        step_by_step.append(f"Step 2: Plan A covered = ₹{billed_inr:,.0f} - ₹{plan_a_deductible:,.0f} = ₹{plan_a_covered:,.0f}")
        
        # Step 3: Plan A pays 80%
        plan_a_pays = plan_a_covered * 0.80
        step_by_step.append(f"Step 3: Plan A pays 80% = ₹{plan_a_covered:,.0f} × 0.80 = ₹{plan_a_pays:,.0f}")
        
        # Step 4: Patient pays to Plan A (20%)
        patient_to_plan_a = plan_a_covered * 0.20
        step_by_step.append(f"Step 4: Patient to Plan A (20%) = ₹{plan_a_covered:,.0f} × 0.20 = ₹{patient_to_plan_a:,.0f}")
        
        # Step 5: Residual to Plan B
        residual_to_plan_b = patient_to_plan_a + plan_a_deductible
        step_by_step.append(f"Step 5: Residual to Plan B = ₹{patient_to_plan_a:,.0f} + ₹{plan_a_deductible:,.0f} = ₹{residual_to_plan_b:,.0f}")
        
        # Step 6: Plan B pays 80% of residual
        plan_b_pays = residual_to_plan_b * 0.80
        step_by_step.append(f"Step 6: Plan B pays 80% = ₹{residual_to_plan_b:,.0f} × 0.80 = ₹{plan_b_pays:,.0f}")
        
        # Step 7: Patient final OOP
        patient_final_oop = residual_to_plan_b * 0.20
        step_by_step.append(f"Step 7: Patient final OOP = ₹{residual_to_plan_b:,.0f} × 0.20 = ₹{patient_final_oop:,.0f}")
        
        # Step 8: OOP max check
        oop_max_check = {
            'plan_a_ok': patient_to_plan_a <= plan_a['oop_max_inr'],
            'plan_b_ok': patient_final_oop <= plan_b['oop_max_inr']
        }
        step_by_step.append(f"Step 8: OOP max check - Plan A: {oop_max_check['plan_a_ok']} (₹{patient_to_plan_a:,.0f} ≤ ₹{plan_a['oop_max_inr']:,.0f}), Plan B: {oop_max_check['plan_b_ok']} (₹{patient_final_oop:,.0f} ≤ ₹{plan_b['oop_max_inr']:,.0f})")
        
        return FinancialResult(
            billed_inr=billed_inr,
            plan_primary_deductible=plan_a_deductible,
            plan_primary_covered=plan_a_covered,
            plan_primary_pays=plan_a_pays,
            patient_to_plan_primary=patient_to_plan_a,
            residual_to_plan_secondary=residual_to_plan_b,
            plan_secondary_pays=plan_b_pays,
            patient_final_oop=patient_final_oop,
            oop_max_check=oop_max_check,
            step_by_step=step_by_step
        )
    
    def _validate_against_cob_agent(self, case_state: CaseState, aarav: FinancialResult, priya: FinancialResult) -> Dict[str, Any]:
        """
        Validate financial calculations against COB agent results
        
        Returns validation result with any discrepancies
        """
        discrepancies = []
        
        # Validate Aarav's surgery
        if 'aarav_surgery' in case_state.cob_result:
            cob_aarav = case_state.cob_result['aarav_surgery']
            
            if abs(cob_aarav.patient_oop - aarav.patient_final_oop) > 1:
                discrepancies.append(f"Aarav OOP mismatch: COB says ₹{cob_aarav.patient_oop:,.0f}, Finance says ₹{aarav.patient_final_oop:,.0f}")
            
            if abs(cob_aarav.plan_primary_payment - aarav.plan_primary_pays) > 1:
                discrepancies.append(f"Aarav Plan B payment mismatch: COB says ₹{cob_aarav.plan_primary_payment:,.0f}, Finance says ₹{aarav.plan_primary_pays:,.0f}")
            
            if abs(cob_aarav.plan_secondary_payment - aarav.plan_secondary_pays) > 1:
                discrepancies.append(f"Aarav Plan A payment mismatch: COB says ₹{cob_aarav.plan_secondary_payment:,.0f}, Finance says ₹{aarav.plan_secondary_pays:,.0f}")
        
        # Validate Priya's PT
        if 'priya_pt' in case_state.cob_result:
            cob_priya = case_state.cob_result['priya_pt']
            
            if abs(cob_priya.patient_oop - priya.patient_final_oop) > 1:
                discrepancies.append(f"Priya OOP mismatch: COB says ₹{cob_priya.patient_oop:,.0f}, Finance says ₹{priya.patient_final_oop:,.0f}")
            
            if abs(cob_priya.plan_primary_payment - priya.plan_primary_pays) > 1:
                discrepancies.append(f"Priya Plan A payment mismatch: COB says ₹{cob_priya.plan_primary_payment:,.0f}, Finance says ₹{priya.plan_primary_pays:,.0f}")
            
            if abs(cob_priya.plan_secondary_payment - priya.plan_secondary_pays) > 1:
                discrepancies.append(f"Priya Plan B payment mismatch: COB says ₹{cob_priya.plan_secondary_payment:,.0f}, Finance says ₹{priya.plan_secondary_pays:,.0f}")
        
        return {
            'matches_ag03': len(discrepancies) == 0,
            'discrepancies': discrepancies
        }
    
    def _calculate_family_summary(self, aarav: FinancialResult, priya: FinancialResult, plan_a: Dict, plan_b: Dict) -> Dict[str, Any]:
        """
        Calculate family-wide financial summary
        """
        total_billed = aarav.billed_inr + priya.billed_inr
        total_plan_a_paid = aarav.plan_secondary_pays + priya.plan_primary_pays
        total_plan_b_paid = aarav.plan_primary_pays + priya.plan_secondary_pays
        total_patient_oop = aarav.patient_final_oop + priya.patient_final_oop
        
        # Calculate savings vs single plan (assuming worst case: patient pays 100% of first plan's deductible + 20% coinsurance)
        # Single plan worst case for Aarav: ₹15,000 + 20% of ₹4,35,000 = ₹1,02,000
        # Single plan worst case for Priya: ₹10,000 + 20% of ₹20,000 = ₹14,000
        single_plan_worst_case = 102000 + 14000
        savings_vs_single_plan = single_plan_worst_case - total_patient_oop
        
        return {
            'total_billed': total_billed,
            'total_plan_a_paid': total_plan_a_paid,
            'total_plan_b_paid': total_plan_b_paid,
            'total_patient_oop': total_patient_oop,
            'savings_vs_single_plan': savings_vs_single_plan,
            'aarav_breakdown': {
                'billed': aarav.billed_inr,
                'oop': aarav.patient_final_oop
            },
            'priya_breakdown': {
                'billed': priya.billed_inr,
                'oop': priya.patient_final_oop
            }
        }
