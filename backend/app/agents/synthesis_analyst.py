"""
Madhyastha — Agent 2: Synthesis Analyst
Analyzes both party statements and generates settlement options
"""

import json
import logging
from typing import Dict, List, Optional
from app.services.groq_service import groq_service
from app.prompts.mediator_prompts import SYNTHESIS_SYSTEM_PROMPT

logger = logging.getLogger("madhyastha.agent.synthesis")


class SynthesisAnalyst:
    """Analyzes both party statements and generates settlement options with RAG precedents"""

    async def analyze(
        self,
        dispute_context: dict,
        statement_a: dict,
        statement_b: dict,
        rag_precedents: Optional[List[dict]] = None,
    ) -> dict:
        """
        Analyze both statements and generate synthesis.
        Returns structured synthesis with conflict zones, overlap zones, and settlement options.
        """
        # Format RAG precedents
        precedents_text = "No precedents available."
        if rag_precedents:
            precedents_text = "\n".join([
                f"- {p.get('case_id', 'N/A')}: {p.get('summary', 'No summary')} "
                f"(Type: {p.get('dispute_type', 'N/A')}, "
                f"Resolution: {p.get('resolution', 'N/A')})"
                for p in rag_precedents
            ])

        system_prompt = SYNTHESIS_SYSTEM_PROMPT.format(
            dispute_type=dispute_context.get("dispute_type", "other_civil"),
            dispute_title=dispute_context.get("title", "Dispute"),
            position_a=statement_a.get("position", "Not stated"),
            interest_a=statement_a.get("interest", "Not stated"),
            min_acceptable_a=statement_a.get("min_acceptable", "Not stated"),
            emotional_need_a=statement_a.get("emotional_need", "Not stated"),
            position_b=statement_b.get("position", "Not stated"),
            interest_b=statement_b.get("interest", "Not stated"),
            min_acceptable_b=statement_b.get("min_acceptable", "Not stated"),
            emotional_need_b=statement_b.get("emotional_need", "Not stated"),
            rag_precedents=precedents_text,
        )

        result = await groq_service.chat_json(
            system_prompt=system_prompt,
            user_message="Analyze both statements and generate settlement options.",
            temperature=0.3,
            max_tokens=4096,
        )

        # Validate required fields
        if "settlement_options" not in result:
            logger.warning("Synthesis missing settlement_options, using defaults")
            result = self._default_synthesis()

        logger.info(f"Synthesis complete: {len(result.get('settlement_options', []))} options generated")
        return result

    def _default_synthesis(self) -> dict:
        """Fallback synthesis if AI response is invalid"""
        return {
            "conflict_zones": ["Core disagreement on terms and amounts"],
            "overlap_zones": ["Both parties prefer resolution over litigation"],
            "settlement_options": [
                {
                    "option_id": "A",
                    "title": "Structured Settlement",
                    "terms": "Negotiated amount paid in structured installments",
                    "timeline": "12 months",
                    "enforcement": "Post-dated instruments",
                    "favors": "neutral",
                    "precedent_ref": "Standard mediation precedent"
                }
            ],
            "recommended_opening": (
                "Welcome to this joint session. Both parties have shown willingness to "
                "resolve this matter amicably. Let us review the options together."
            )
        }
