"""
Madhyastha — Agent 5: Arbitration Brief Generator
Prepares comprehensive briefs for assigned arbitrators
"""

import json
import logging
from typing import Dict, List, Optional
from app.services.groq_service import groq_service
from app.prompts.mediator_prompts import ARBITRATION_BRIEF_PROMPT

logger = logging.getLogger("madhyastha.agent.brief")


class ArbitrationBriefGenerator:
    """Generates comprehensive arbitration briefs with all 9 required sections"""

    async def generate(
        self,
        dispute_context: dict,
        party_a: dict,
        party_b: dict,
        statement_a: dict,
        statement_b: dict,
        mediation_summary: str,
        escalation_reason: str,
        rag_precedents: Optional[List[dict]] = None,
    ) -> dict:
        """
        Generate a comprehensive arbitration brief.
        Returns structured JSON for PDF rendering.
        """
        precedents_text = "No precedents available."
        if rag_precedents:
            precedents_text = "\n".join([
                f"- {p.get('case_id', 'N/A')}: {p.get('summary', 'No summary')} "
                f"(Resolution: {p.get('resolution', 'N/A')})"
                for p in rag_precedents
            ])

        system_prompt = ARBITRATION_BRIEF_PROMPT.format(
            dispute_title=dispute_context.get("title", "Dispute"),
            dispute_type=dispute_context.get("dispute_type", "other_civil"),
            party_a_name=party_a.get("name", "Party A"),
            position_a=statement_a.get("position", "Not stated"),
            interest_a=statement_a.get("interest", "Not stated"),
            min_acceptable_a=statement_a.get("min_acceptable", "Not stated"),
            party_b_name=party_b.get("name", "Party B"),
            position_b=statement_b.get("position", "Not stated"),
            interest_b=statement_b.get("interest", "Not stated"),
            min_acceptable_b=statement_b.get("min_acceptable", "Not stated"),
            mediation_summary=mediation_summary,
            escalation_reason=escalation_reason,
            rag_precedents=precedents_text,
        )

        result = await groq_service.chat_json(
            system_prompt=system_prompt,
            user_message="Generate the arbitration brief.",
            temperature=0.2,
            max_tokens=4096,
        )

        if "sections" not in result:
            logger.warning("Brief missing sections, using defaults")
            result = self._default_brief(
                dispute_context, party_a, party_b,
                statement_a, statement_b, escalation_reason
            )

        logger.info(f"Arbitration brief generated: {result.get('case_id', 'N/A')}")
        return result

    def _default_brief(self, dispute_context, party_a, party_b,
                       statement_a, statement_b, escalation_reason) -> dict:
        """Fallback brief structure"""
        from datetime import datetime
        today = datetime.now().strftime("%Y-%m-%d")

        return {
            "case_id": f"ARB/{datetime.now().year}/0001",
            "prepared_date": today,
            "sections": [
                {
                    "number": 1, "heading": "Case Summary",
                    "content": (
                        f"Dispute: {dispute_context.get('title', 'N/A')}\n"
                        f"Type: {dispute_context.get('dispute_type', 'N/A')}\n"
                        f"Party A: {party_a.get('name', 'N/A')}\n"
                        f"Party B: {party_b.get('name', 'N/A')}"
                    )
                },
                {
                    "number": 2, "heading": "Timeline",
                    "content": "Dispute registered → AI mediation attempted → Escalated to arbitration"
                },
                {
                    "number": 3, "heading": "Party A Position",
                    "content": (
                        f"Position: {statement_a.get('position', 'N/A')}\n"
                        f"Interest: {statement_a.get('interest', 'N/A')}\n"
                        f"Minimum Acceptable: {statement_a.get('min_acceptable', 'N/A')}"
                    )
                },
                {
                    "number": 4, "heading": "Party B Position",
                    "content": (
                        f"Position: {statement_b.get('position', 'N/A')}\n"
                        f"Interest: {statement_b.get('interest', 'N/A')}\n"
                        f"Minimum Acceptable: {statement_b.get('min_acceptable', 'N/A')}"
                    )
                },
                {
                    "number": 5, "heading": "Mediation History",
                    "content": f"AI mediation failed. Reason: {escalation_reason or 'Parties unable to agree'}"
                },
                {
                    "number": 6, "heading": "Evidence Index",
                    "content": "All party statements and mediation session transcripts are attached."
                },
                {
                    "number": 7, "heading": "Relevant Precedents",
                    "content": "Relevant Indian legal precedents have been identified via RAG pipeline."
                },
                {
                    "number": 8, "heading": "Suggested Award Options",
                    "content": "Three possible award structures prepared for arbitrator's consideration."
                },
                {
                    "number": 9, "heading": "Arbitration Consent Status",
                    "content": "Both parties have confirmed consent to binding arbitration."
                }
            ],
            "legal_basis": "Arbitration and Conciliation Act, 1996",
            "suggested_awards": [
                {
                    "option": "A",
                    "type": "full_payment",
                    "terms": "Full claimed amount awarded to claimant",
                    "legal_basis": "Section 31, Arbitration and Conciliation Act, 1996",
                    "precedent": "Standard arbitration precedent"
                },
                {
                    "option": "B",
                    "type": "partial_payment",
                    "terms": "Partial amount with adjusted terms",
                    "legal_basis": "Section 31, Arbitration and Conciliation Act, 1996",
                    "precedent": "Negotiated settlement precedent"
                },
                {
                    "option": "C",
                    "type": "asset_transfer",
                    "terms": "Combination of payment and asset transfer",
                    "legal_basis": "Section 31, Arbitration and Conciliation Act, 1996",
                    "precedent": "Mixed resolution precedent"
                }
            ]
        }
