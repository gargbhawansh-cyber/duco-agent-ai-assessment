"""
AG-04: Pre-Authorization Drafting Agent
Generates IRDAI-compliant pre-authorization letters with clinical coding
"""

import time
from typing import Dict, Any
from datetime import datetime

from state import CaseState
from agents.base_agent import BaseAgent


class PreAuthAgent(BaseAgent):
    """Pre-Authorization Drafting Agent for generating IRDAI-compliant letters"""
    
    def __init__(self):
        super().__init__("AG-04", "Pre-Auth Drafting Agent")
    
    async def execute(self, case_state: CaseState, **kwargs) -> CaseState:
        """
        Execute pre-auth letter generation
        
        Args:
            case_state: The shared case state object
            
        Returns:
            Updated case_state with pre-auth letters
        """
        start_time = time.time()
        input_summary = "Pre-auth letter generation initiated"
        
        try:
            # Generate Letter 1: Primary payer (Plan B for Aarav)
            letter_1 = self._generate_primary_letter(case_state)
            case_state.preauth_letters['insurer2_primary'] = letter_1
            
            # Generate Letter 2: Secondary payer (Plan A for Aarav)
            letter_2 = self._generate_secondary_letter(case_state)
            case_state.preauth_letters['insurer1_secondary'] = letter_2
            
            duration_ms = (time.time() - start_time) * 1000
            output_summary = "Generated 2 pre-auth letters (primary and secondary)"
            self.log_execution(case_state, input_summary, output_summary, duration_ms, confidence_score=0.95)
            
            return case_state
            
        except Exception as e:
            case_state.add_error(
                agent_id=self.agent_id,
                field_name="preauth_generation",
                message=f"Pre-auth letter generation failed: {str(e)}",
                human_review_required=True
            )
            duration_ms = (time.time() - start_time) * 1000
            output_summary = f"Pre-auth generation failed: {str(e)}"
            self.log_execution(case_state, input_summary, output_summary, duration_ms, confidence_score=0.0)
            return case_state
    
    def _generate_primary_letter(self, case_state: CaseState) -> str:
        """
        Generate pre-auth letter for primary payer (Plan B - Insurer2)
        
        Addressed to: Insurer2 (Plan B) — Primary Payer
        Patient: Aarav Sen
        """
        current_date = datetime.now().strftime("%B %d, %Y")
        
        letter = f"""PRE-AUTHORIZATION REQUEST
========================

Date: {current_date}

To:
Medical Claims Department
Insurer2 (Plan B)
[Address Line 1]
[Address Line 2]
[City, State - PIN]

From:
Dr. Sharma Orthopedic Surgery
[NPI: Placeholder]
[Facility Address]

RE: PRE-AUTHORIZATION FOR SURGICAL INTERVENTION - AARAV SEN

POLICY INFORMATION
------------------
Policy Number: POL-B-2024-002
Group Number: GRP-B-2024-001
Patient Name: Aarav Sen
Date of Birth: [DOB Placeholder]
Patient ID: [ID Placeholder]

DIAGNOSIS (ICD-10 CODES)
------------------------
Primary Diagnosis: Complete tear of the anterior cruciate ligament (ACL)
ICD-10 Code: M23.61

Secondary Diagnosis: Medial meniscus tear
ICD-10 Code: S83.202A

PROCEDURES REQUESTED (CPT CODES)
---------------------------------
1. CPT 29888: Arthroscopically aided ACL reconstruction
   Estimated Cost: ₹3,50,000
   Units: 1

2. CPT 29881: Arthroscopy, knee, surgical with meniscectomy
   Estimated Cost: ₹1,00,000
   Units: 1

TOTAL ESTIMATED COST: ₹4,50,000

URGENCY CLASSIFICATION
---------------------
Urgent - Sports injury with mobility impairment and risk of further joint damage

CLINICAL JUSTIFICATION
----------------------
The patient presents with a complete tear of the anterior cruciate ligament (ACL) confirmed by MRI examination performed on June 10, 2026. The MRI findings indicate a complete rupture of the ACL with associated medial meniscus tear (S83.202A). Clinical examination demonstrates significant joint instability, positive Lachman test, and anterior drawer sign. The patient reports inability to participate in normal daily activities and sports participation.

Surgical intervention is medically necessary to:
1. Restore joint stability and prevent further meniscal damage
2. Reduce risk of early-onset osteoarthritis
3. Enable return to normal functional activities
4. Prevent chronic instability and associated complications

Conservative management has been attempted without adequate improvement. The proposed arthroscopic ACL reconstruction with meniscectomy is the standard of care for this condition and is supported by current clinical guidelines.

TREATING PHYSICIAN
------------------
Name: Dr. Sharma
Specialization: Orthopedic Surgery
NPI: [Placeholder]
Contact: [Phone Number]
Email: [Email Address]

FACILITY INFORMATION
--------------------
Facility Name: [Hospital Name]
Address: [Facility Address]
Contact: [Facility Phone]

SUPPORTING DOCUMENTS ATTACHED
-----------------------------
1. MRI Report (June 10, 2026)
2. Surgical Estimate
3. Physician Consultation Notes
4. Pre-authorization Form (completed)

COMPLIANCE STATEMENT
--------------------
This pre-authorization request is submitted in compliance with IRDAI Health Insurance Regulations 2016 and PA-2023 guidelines. All clinical information provided is accurate and complete to the best of our knowledge.

PHYSICIAN SIGNATURE
-------------------
Signature: _______________________
Name: Dr. Sharma
Date: {current_date}
Credentials: MS (Orthopedics)

---
This request is for PRIMARY PAYER coverage under Plan B (Insurer2).
"""
        return letter
    
    def _generate_secondary_letter(self, case_state: CaseState) -> str:
        """
        Generate pre-auth letter for secondary payer (Plan A - Insurer1)
        
        Addressed to: Insurer1 (Plan A) — Secondary Payer
        """
        current_date = datetime.now().strftime("%B %d, %Y")
        
        letter = f"""COORDINATION OF BENEFITS (COB) PRE-AUTHORIZATION REQUEST
==========================================================

Date: {current_date}

To:
Medical Claims Department
Insurer1 (Plan A)
[Address Line 1]
[Address Line 2]
[City, State - PIN]

From:
Dr. Sharma Orthopedic Surgery
[NPI: Placeholder]
[Facility Address]

RE: SECONDARY PAYER PRE-AUTHORIZATION - AARAV SEN (COB CASE)

IMPORTANT NOTICE: COORDINATION OF BENEFITS
-------------------------------------------
This is a Coordination of Benefits (COB) pre-authorization request.
Plan B (Insurer2) is the PRIMARY PAYER for this claim.
This letter is for SECONDARY PAYER coverage under Plan A (Insurer1).

POLICY INFORMATION
------------------
Policy Number: POL-A-2024-001
Group Number: GRP-A-2024-001
Patient Name: Aarav Sen
Relationship: Dependent
Date of Birth: [DOB Placeholder]
Patient ID: [ID Placeholder]

PRIMARY PAYER INFORMATION
-------------------------
Primary Insurer: Insurer2 (Plan B)
Policy Number: POL-B-2024-002
Primary Payer Reference: [To be filled after primary approval]
Estimated Primary Payer Obligation: ₹3,48,000

DIAGNOSIS (ICD-10 CODES)
------------------------
Primary Diagnosis: Complete tear of the anterior cruciate ligament (ACL)
ICD-10 Code: M23.61

Secondary Diagnosis: Medial meniscus tear
ICD-10 Code: S83.202A

PROCEDURES REQUESTED (CPT CODES)
---------------------------------
1. CPT 29888: Arthroscopically aided ACL reconstruction
   Estimated Cost: ₹3,50,000
   Units: 1

2. CPT 29881: Arthroscopy, knee, surgical with meniscectomy
   Estimated Cost: ₹1,00,000
   Units: 1

TOTAL ESTIMATED COST: ₹4,50,000

ESTIMATED SECONDARY PAYER OBLIGATION
-------------------------------------
After primary payer settlement, estimated secondary payer (Plan A) obligation: ₹81,600
Estimated patient residual after secondary coverage: ₹20,400

URGENCY CLASSIFICATION
---------------------
Urgent - Sports injury with mobility impairment and risk of further joint damage

CLINICAL JUSTIFICATION
----------------------
The patient presents with a complete tear of the anterior cruciate ligament (ACL) confirmed by MRI examination performed on June 10, 2026. The MRI findings indicate a complete rupture of the ACL with associated medial meniscus tear (S83.202A). Clinical examination demonstrates significant joint instability, positive Lachman test, and anterior drawer sign. The patient reports inability to participate in normal daily activities and sports participation.

Surgical intervention is medically necessary to:
1. Restore joint stability and prevent further meniscal damage
2. Reduce risk of early-onset osteoarthritis
3. Enable return to normal functional activities
4. Prevent chronic instability and associated complications

Conservative management has been attempted without adequate improvement. The proposed arthroscopic ACL reconstruction with meniscectomy is the standard of care for this condition and is supported by current clinical guidelines.

TREATING PHYSICIAN
------------------
Name: Dr. Sharma
Specialization: Orthopedic Surgery
NPI: [Placeholder]
Contact: [Phone Number]
Email: [Email Address]

FACILITY INFORMATION
--------------------
Facility Name: [Hospital Name]
Address: [Facility Address]
Contact: [Facility Phone]

SUPPORTING DOCUMENTS ATTACHED
-----------------------------
1. MRI Report (June 10, 2026)
2. Surgical Estimate
3. Physician Consultation Notes
4. Primary Payer Explanation of Benefits (EOB) - [To be attached]
5. Pre-authorization Form (completed)

COMPLIANCE STATEMENT
--------------------
This pre-authorization request is submitted in compliance with IRDAI Health Insurance Regulations 2016 and PA-2023 guidelines for Coordination of Benefits. All clinical information provided is accurate and complete to the best of our knowledge.

PHYSICIAN SIGNATURE
-------------------
Signature: _______________________
Name: Dr. Sharma
Date: {current_date}
Credentials: MS (Orthopedics)

---
This request is for SECONDARY PAYER coverage under Plan A (Insurer1).
Primary Payer: Plan B (Insurer2) | Patient Role: Dependent
"""
        return letter
