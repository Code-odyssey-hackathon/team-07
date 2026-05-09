"""
Madhyastha — Agent 4: Agreement Drafter
Generates legally compliant mediation settlement agreements
"""

import json
import logging
from typing import Dict, Optional
from app.services.groq_service import groq_service
from app.prompts.mediator_prompts import AGREEMENT_DRAFTER_PROMPT

logger = logging.getLogger("madhyastha.agent.agreement")


class AgreementDrafter:
    """Generates mediation settlement agreements under Mediation Act 2023, Section 22"""

    async def draft(
        self,
        dispute_context: dict,
        party_a: dict,
        party_b: dict,
        agreed_option: dict,
    ) -> dict:
        """
        Generate a legally compliant agreement document.
        Returns structured JSON for PDF rendering.
        """
        system_prompt = AGREEMENT_DRAFTER_PROMPT.format(
            dispute_title=dispute_context.get("title", "Dispute"),
            dispute_type=dispute_context.get("dispute_type", "other_civil"),
            party_a_name=party_a.get("name", "Party A"),
            party_a_email=party_a.get("email", "N/A"),
            party_a_phone=party_a.get("phone", "N/A"),
            party_b_name=party_b.get("name", "Party B"),
            party_b_email=party_b.get("email", "N/A"),
            party_b_phone=party_b.get("phone", "N/A"),
            agreed_option=json.dumps(agreed_option.get("option", {}), indent=2),
            settlement_terms=agreed_option.get("terms", "As negotiated"),
        )

        result = await groq_service.chat_json(
            system_prompt=system_prompt,
            user_message="Generate the mediation settlement agreement.",
            temperature=0.2,
            max_tokens=4096,
        )

        # Validate required fields
        if "sections" not in result:
            logger.warning("Agreement missing sections, using defaults")
            result = self._default_agreement(dispute_context, party_a, party_b, agreed_option)

        logger.info(f"Agreement drafted: {result.get('reference_number', 'N/A')}")
        return result

    def _default_agreement(self, dispute_context, party_a, party_b, agreed_option) -> dict:
        """Fallback agreement structure"""
        from datetime import datetime
        today = datetime.now().strftime("%Y-%m-%d")

        return {
            "title": "Mediation Settlement Agreement",
            "date": today,
            "reference_number": f"MSA/{datetime.now().year}/0001",
            "legal_basis": "Section 22, Mediation Act, 2023",
            "sections": [
                {
                    "heading": "1. Parties",
                    "content": (
                        f"This Mediation Settlement Agreement is entered into between:\n"
                        f"Party A: {party_a.get('name', 'N/A')} "
                        f"(Contact: {party_a.get('email', 'N/A')}, {party_a.get('phone', 'N/A')})\n"
                        f"Party B: {party_b.get('name', 'N/A')} "
                        f"(Contact: {party_b.get('email', 'N/A')}, {party_b.get('phone', 'N/A')})"
                    )
                },
                {
                    "heading": "2. Dispute Description",
                    "content": (
                        f"The parties were in a civil dispute regarding: "
                        f"{dispute_context.get('title', 'the matter in question')} "
                        f"(Type: {dispute_context.get('dispute_type', 'civil')})"
                    )
                },
                {
                    "heading": "3. Agreed Terms",
                    "content": (
                        f"After due mediation, the parties have agreed to the following terms:\n"
                        f"{agreed_option.get('terms', 'As negotiated during the mediation session.')}"
                    )
                },
                {
                    "heading": "4. Payment Schedule",
                    "content": "Payment shall be made as per the agreed terms and timeline stated above."
                },
                {
                    "heading": "5. Default Clause",
                    "content": (
                        "In the event of non-compliance by either party, the aggrieved party "
                        "shall be entitled to approach the appropriate court of competent jurisdiction "
                        "for enforcement of this agreement."
                    )
                },
                {
                    "heading": "6. Signatures",
                    "content": (
                        f"Party A: {party_a.get('name', '_____________')}\n"
                        f"Party B: {party_b.get('name', '_____________')}\n"
                        f"AI Mediation System: Madhyastha Platform\n"
                        f"Date: {today}"
                    )
                },
                {
                    "heading": "7. Legal Citation",
                    "content": (
                        "This agreement is executed under Section 22 of the Mediation Act, 2023, "
                        "and is binding and enforceable in all courts of competent jurisdiction in India."
                    )
                }
            ],
            "enforcement_note": (
                "This agreement is binding and enforceable as per Section 22 "
                "of the Mediation Act, 2023."
            )
        }
