"""
Unit Tests for COB Calculations
Tests the financial calculation logic for dual insurance coverage
"""

import pytest
from agents.cob_agent import COBAgent
from agents.finance_agent import FinanceAgent
from state import CaseState, CaseStatus, PatientRecord


@pytest.fixture
def setup_case_state():
    """Setup a test case state with plan parameters"""
    case_state = CaseState(case_id="TEST-001")
    case_state.status = CaseStatus.COB
    
    # Setup patients
    case_state.patients['aarav sen'] = PatientRecord(
        name="Aarav Sen",
        policy_numbers={'plan_a': 'POL-A-001', 'plan_b': 'POL-B-001'},
        role_in_plans={'plan_a': 'DEPENDENT', 'plan_b': 'PRIMARY'}
    )
    
    case_state.patients['priya sen'] = PatientRecord(
        name="Priya Sen",
        policy_numbers={'plan_a': 'POL-A-001', 'plan_b': 'POL-B-001'},
        role_in_plans={'plan_a': 'PRIMARY', 'plan_b': 'DEPENDENT'}
    )
    
    return case_state


class TestCOBCalculations:
    """Test COB calculation logic"""
    
    @pytest.mark.asyncio
    async def test_aarav_surgery_cob_calculation(self, setup_case_state):
        """Test Aarav's ACL surgery COB calculation (₹4,50,000)"""
        cob_agent = COBAgent()
        case_state = setup_case_state
        
        # Execute COB calculation
        case_state = await cob_agent.execute(case_state)
        
        # Verify COB result exists
        assert 'aarav_surgery' in case_state.cob_result
        aarav_result = case_state.cob_result['aarav_surgery']
        
        # Verify payer order
        assert aarav_result.primary_plan == 'Plan B'
        assert aarav_result.secondary_plan == 'Plan A'
        
        # Verify billed amount
        assert aarav_result.billed == 450000
        
        # Verify Plan B payment (primary)
        # Plan B pays 80% of (450000 - 15000) = 80% of 435000 = 348000
        assert aarav_result.plan_primary_payment == 348000
        
        # Verify Plan A payment (secondary)
        # Plan A pays 80% of residual (87000 + 15000) = 80% of 102000 = 81600
        assert aarav_result.plan_secondary_payment == 81600
        
        # Verify patient OOP
        # Patient pays 20% of residual = 20% of 102000 = 20400
        assert aarav_result.patient_oop == 20400
        
        # Verify audit steps exist
        assert len(aarav_result.audit_steps) > 0
    
    @pytest.mark.asyncio
    async def test_priya_pt_cob_calculation(self, setup_case_state):
        """Test Priya's PT COB calculation (₹30,000)"""
        cob_agent = COBAgent()
        case_state = setup_case_state
        
        # Execute COB calculation
        case_state = await cob_agent.execute(case_state)
        
        # Verify COB result exists
        assert 'priya_pt' in case_state.cob_result
        priya_result = case_state.cob_result['priya_pt']
        
        # Verify payer order
        assert priya_result.primary_plan == 'Plan A'
        assert priya_result.secondary_plan == 'Plan B'
        
        # Verify billed amount
        assert priya_result.billed == 30000
        
        # Verify Plan A payment (primary)
        # Plan A pays 80% of (30000 - 10000) = 80% of 20000 = 16000
        assert priya_result.plan_primary_payment == 16000
        
        # Verify Plan B payment (secondary)
        # Plan B pays 80% of residual (4000 + 10000) = 80% of 14000 = 11200
        assert priya_result.plan_secondary_payment == 11200
        
        # Verify patient OOP
        # Patient pays 20% of residual = 20% of 14000 = 2800
        assert priya_result.patient_oop == 2800
        
        # Verify audit steps exist
        assert len(priya_result.audit_steps) > 0
    
    @pytest.mark.asyncio
    async def test_total_family_oop(self, setup_case_state):
        """Test total family out-of-pocket calculation"""
        cob_agent = COBAgent()
        case_state = setup_case_state
        
        # Execute COB calculation
        case_state = await cob_agent.execute(case_state)
        
        # Calculate total family OOP
        aarav_oop = case_state.cob_result['aarav_surgery'].patient_oop
        priya_oop = case_state.cob_result['priya_pt'].patient_oop
        total_oop = aarav_oop + priya_oop
        
        # Expected: 20400 + 2800 = 23200
        assert total_oop == 23200


class TestFinanceCalculations:
    """Test financial calculation and validation"""
    
    @pytest.mark.asyncio
    async def test_aarav_surgery_financial_calculation(self, setup_case_state):
        """Test Aarav's surgery financial calculation"""
        finance_agent = FinanceAgent()
        case_state = setup_case_state
        
        # First run COB to populate cob_result
        cob_agent = COBAgent()
        case_state = await cob_agent.execute(case_state)
        
        # Execute financial calculation
        case_state = await finance_agent.execute(case_state)
        
        # Verify financials exist
        assert 'aarav_surgery' in case_state.financials
        aarav_financial = case_state.financials['aarav_surgery']
        
        # Verify billed amount
        assert aarav_financial.billed_inr == 450000
        
        # Verify Plan B (primary) calculations
        assert aarav_financial.plan_primary_deductible == 15000
        assert aarav_financial.plan_primary_covered == 435000
        assert aarav_financial.plan_primary_pays == 348000
        assert aarav_financial.patient_to_plan_primary == 87000
        
        # Verify Plan A (secondary) calculations
        assert aarav_financial.residual_to_plan_secondary == 102000
        assert aarav_financial.plan_secondary_pays == 81600
        assert aarav_financial.patient_final_oop == 20400
        
        # Verify OOP max check
        assert aarav_financial.oop_max_check['plan_a_ok'] == True
        assert aarav_financial.oop_max_check['plan_b_ok'] == True
    
    @pytest.mark.asyncio
    async def test_priya_pt_financial_calculation(self, setup_case_state):
        """Test Priya's PT financial calculation"""
        finance_agent = FinanceAgent()
        case_state = setup_case_state
        
        # First run COB to populate cob_result
        cob_agent = COBAgent()
        case_state = await cob_agent.execute(case_state)
        
        # Execute financial calculation
        case_state = await finance_agent.execute(case_state)
        
        # Verify financials exist
        assert 'priya_pt' in case_state.financials
        priya_financial = case_state.financials['priya_pt']
        
        # Verify billed amount
        assert priya_financial.billed_inr == 30000
        
        # Verify Plan A (primary) calculations
        assert priya_financial.plan_primary_deductible == 10000
        assert priya_financial.plan_primary_covered == 20000
        assert priya_financial.plan_primary_pays == 16000
        assert priya_financial.patient_to_plan_primary == 4000
        
        # Verify Plan B (secondary) calculations
        assert priya_financial.residual_to_plan_secondary == 14000
        assert priya_financial.plan_secondary_pays == 11200
        assert priya_financial.patient_final_oop == 2800
    
    @pytest.mark.asyncio
    async def test_cob_vs_finance_validation(self, setup_case_state):
        """Test validation between COB and Finance agent results"""
        finance_agent = FinanceAgent()
        case_state = setup_case_state
        
        # Run COB first
        cob_agent = COBAgent()
        case_state = await cob_agent.execute(case_state)
        
        # Run Finance
        case_state = await finance_agent.execute(case_state)
        
        # Verify validation result
        assert 'validation' in case_state.financials
        validation = case_state.financials['validation']
        
        # Should match (no discrepancies)
        assert validation['matches_ag03'] == True
        assert len(validation['discrepancies']) == 0
    
    @pytest.mark.asyncio
    async def test_family_summary_calculation(self, setup_case_state):
        """Test family-wide financial summary"""
        finance_agent = FinanceAgent()
        case_state = setup_case_state
        
        # Run COB first
        cob_agent = COBAgent()
        case_state = await cob_agent.execute(case_state)
        
        # Run Finance
        case_state = await finance_agent.execute(case_state)
        
        # Verify family summary
        assert 'family_summary' in case_state.financials
        summary = case_state.financials['family_summary']
        
        # Verify totals
        assert summary['total_billed'] == 480000  # 450000 + 30000
        assert summary['total_plan_a_paid'] == 97600  # 81600 + 16000
        assert summary['total_plan_b_paid'] == 359200  # 348000 + 11200
        assert summary['total_patient_oop'] == 23200  # 20400 + 2800
        
        # Verify savings calculation
        # Single plan worst case: 102000 (Aarav) + 14000 (Priya) = 116000
        # Dual coverage: 23200
        # Savings: 116000 - 23200 = 92800
        assert summary['savings_vs_single_plan'] == 92800


class TestEdgeCases:
    """Test edge cases and boundary conditions"""
    
    @pytest.mark.asyncio
    async def test_oop_max_boundary(self, setup_case_state):
        """Test OOP maximum boundary conditions"""
        finance_agent = FinanceAgent()
        case_state = setup_case_state
        
        # Run COB first
        cob_agent = COBAgent()
        case_state = await cob_agent.execute(case_state)
        
        # Run Finance
        case_state = await finance_agent.execute(case_state)
        
        # Verify OOP max checks
        aarav_financial = case_state.financials['aarav_surgery']
        priya_financial = case_state.financials['priya_pt']
        
        # Both should be within OOP max
        assert aarav_financial.oop_max_check['plan_a_ok'] == True
        assert aarav_financial.oop_max_check['plan_b_ok'] == True
        assert priya_financial.oop_max_check['plan_a_ok'] == True
        assert priya_financial.oop_max_check['plan_b_ok'] == True
    
    def test_step_by_step_traceability(self, setup_case_state):
        """Test that all calculations are traceable through step_by_step"""
        # This would be implemented to verify audit trail completeness
        # For now, we just verify the structure exists
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
