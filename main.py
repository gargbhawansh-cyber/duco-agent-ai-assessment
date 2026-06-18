"""
DuCO-Agent - Dual Coverage Optimization Agentic AI System
Main Entry Point
"""

import asyncio
import sys
import json
import uuid
from datetime import datetime
from pathlib import Path

from state import CaseState, CaseStatus
from agents import SupervisorAgent


async def main():
    """Main execution function for DuCO-Agent"""
    
    print("=" * 60)
    print("DuCO-Agent - Dual Coverage Optimization AI System")
    print("=" * 60)
    print()
    
    # Generate unique case ID
    case_id = f"CASE-{uuid.uuid4().hex[:8].upper()}"
    print(f"Case ID: {case_id}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Initialize case state
    case_state = CaseState(case_id=case_id)
    
    # Initialize Supervisor Agent
    supervisor = SupervisorAgent()
    
    # Mock document paths (in production, these would be real file paths)
    document_paths = {
        'pt_invoice': 'mock_documents/pt_invoice_mock.txt',
        'mri_report': 'mock_documents/mri_report_mock.txt',
        'surgeon_estimate': 'mock_documents/surgeon_estimate_mock.txt'
    }
    
    # Load user query
    with open('mock_documents/user_query.txt', 'r') as f:
        user_query = f.read()
    
    print("Processing documents and query...")
    print(f"Documents: {len(document_paths)} files")
    print(f"User query: {len(user_query)} characters")
    print()
    
    # Execute the agent pipeline
    print("Starting agent pipeline...")
    print("-" * 60)
    
    try:
        case_state = await supervisor.execute(
            case_state,
            document_paths=document_paths,
            user_query=user_query
        )
        
        print("-" * 60)
        print()
        
        # Display results
        print("PIPELINE COMPLETED")
        print("=" * 60)
        print(f"Final Status: {case_state.status.value}")
        print(f"Total Duration: {sum(log.duration_ms for log in case_state.agent_logs):.2f} ms")
        print(f"Agents Executed: {len(case_state.agent_logs)}")
        print(f"Errors: {len(case_state.errors)}")
        print()
        
        # Display financial summary
        if case_state.financials:
            print("FINANCIAL SUMMARY")
            print("-" * 60)
            family_summary = case_state.financials.get('family_summary', {})
            print(f"Total Billed: ₹{family_summary.get('total_billed', 0):,.0f}")
            print(f"Plan A Paid: ₹{family_summary.get('total_plan_a_paid', 0):,.0f}")
            print(f"Plan B Paid: ₹{family_summary.get('total_plan_b_paid', 0):,.0f}")
            print(f"Patient OOP: ₹{family_summary.get('total_patient_oop', 0):,.0f}")
            print(f"Savings vs Single Plan: ₹{family_summary.get('savings_vs_single_plan', 0):,.0f}")
            print()
        
        # Display agent execution logs
        print("AGENT EXECUTION LOGS")
        print("-" * 60)
        for log in case_state.agent_logs:
            print(f"{log.agent_id} ({log.agent_name})")
            print(f"  Duration: {log.duration_ms:.2f} ms")
            print(f"  Confidence: {log.confidence_score:.2f}")
            print(f"  Input: {log.input_summary[:50]}...")
            print(f"  Output: {log.output_summary[:50]}...")
            print()
        
        # Display errors if any
        if case_state.errors:
            print("ERRORS")
            print("-" * 60)
            for error in case_state.errors:
                print(f"Agent: {error.agent_id}")
                print(f"Field: {error.field_name}")
                print(f"Message: {error.message}")
                print(f"Human Review Required: {error.human_review_required}")
                print()
        
        # Save outputs to files
        print("SAVING OUTPUTS")
        print("-" * 60)
        output_dir = Path("outputs")
        output_dir.mkdir(exist_ok=True)
        
        # Save patient briefing
        if 'patient_briefing' in case_state.outputs:
            with open(output_dir / "patient_briefing.txt", 'w') as f:
                f.write(case_state.outputs['patient_briefing'])
            print("✓ Patient briefing saved")
        
        # Save patient briefing audio
        if 'patient_briefing_audio' in case_state.outputs:
            print(f"✓ Patient briefing audio saved: {case_state.outputs['patient_briefing_audio']}")
            if 'audio_metadata' in case_state.outputs:
                metadata = case_state.outputs['audio_metadata']
                print(f"  Duration: {metadata.get('duration_seconds', 0):.1f}s")
        
        # Save cost flow visual
        if 'cost_flow_visual' in case_state.outputs:
            with open(output_dir / "cost_flow_visual.json", 'w') as f:
                json.dump(case_state.outputs['cost_flow_visual'], f, indent=2)
            print("✓ Cost flow visual saved")
        
        # Save Sankey diagram
        if 'sankey_diagram_path' in case_state.outputs:
            print(f"✓ Sankey diagram saved: {case_state.outputs['sankey_diagram_path']}")
        
        # Save interactive visualization
        if 'interactive_visualization_path' in case_state.outputs:
            print(f"✓ Interactive visualization saved: {case_state.outputs['interactive_visualization_path']}")
        
        # Save financial summary table
        if 'financial_summary_table' in case_state.outputs:
            with open(output_dir / "financial_summary.md", 'w') as f:
                f.write(case_state.outputs['financial_summary_table'])
            print("✓ Financial summary table saved")
        
        # Save pre-auth letters
        if 'preauth_package' in case_state.outputs:
            preauth_package = case_state.outputs['preauth_package']
            with open(output_dir / "preauth_instructions.txt", 'w') as f:
                f.write(preauth_package['cover_note'])
            print("✓ Pre-auth instructions saved")
            
            for letter_name, letter_content in preauth_package['letters'].items():
                filename = f"preauth_{letter_name}.txt"
                with open(output_dir / filename, 'w') as f:
                    f.write(letter_content)
                print(f"✓ Pre-auth letter saved: {filename}")
        
        # Save audit summary
        if 'audit_summary' in case_state.outputs:
            with open(output_dir / "audit_summary.json", 'w') as f:
                json.dump(case_state.outputs['audit_summary'], f, indent=2)
            print("✓ Audit summary saved")
        
        # Save full case state
        with open(output_dir / f"case_state_{case_id}.json", 'w') as f:
            json.dump(case_state.to_dict(), f, indent=2)
        print(f"✓ Full case state saved")
        
        print()
        print("=" * 60)
        print("DuCO-Agent execution completed successfully!")
        print(f"Outputs saved to: {output_dir.absolute()}")
        print("=" * 60)
        
        return case_state
        
    except Exception as e:
        print(f"\nERROR: Pipeline execution failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    asyncio.run(main())
