"""
Madhyastha — Agent 3: Joint Mediator
Neutral facilitator in the real-time joint mediation session
"""

import json
import logging
from typing import Dict, List, Optional
from app.services.groq_service import groq_service
from app.prompts.mediator_prompts import JOINT_MEDIATOR_SYSTEM_PROMPT

logger = logging.getLogger("madhyastha.agent.joint")


class JointMediator:
    """Neutral facilitator for the joint mediation session between both parties"""

    def __init__(self, dispute_context: dict, synthesis_data: dict, rag_precedents: str = ""):
        self.dispute_type = dispute_context.get("dispute_type", "other_civil")
        self.dispute_title = dispute_context.get("title", "Dispute")
        self.synthesis_data = synthesis_data
        self.rag_precedents = rag_precedents
        self.max_rounds = 3
        self.escalation_signals = 0

    async def mediate(
        self,
        user_message: str,
        party_role: str,
        party_name: str,
        current_round: int,
        session_history: Optional[List[dict]] = None,
    ) -> dict:
        """
        Process a message in the joint session.
        Returns: {
            "ai_response": str,
            "signal": Optional[str],  # AGREEMENT_REACHED | ESCALATE_TO_ARBITRATION
            "agreed_option": Optional[str]
        }
        """
        # Format session history
        history_text = "No previous messages."
        if session_history:
            history_text = "\n".join([
                f"[{msg.get('role', 'unknown')}] {msg.get('party_name', '')}: {msg.get('content', '')}"
                for msg in session_history[-20:]  # Last 20 messages
            ])

        system_prompt = JOINT_MEDIATOR_SYSTEM_PROMPT.format(
            dispute_type=self.dispute_type,
            dispute_title=self.dispute_title,
            current_round=current_round,
            max_rounds=self.max_rounds,
            synthesis_data=json.dumps(self.synthesis_data, indent=2),
            rag_precedents=self.rag_precedents,
            session_history=history_text,
        )

        prefixed_message = f"[{party_role} - {party_name}]: {user_message}"

        response = await groq_service.chat(
            system_prompt=system_prompt,
            user_message=prefixed_message,
            temperature=0.6,
            max_tokens=1024,
        )

        # Check for signals
        signal = None
        agreed_option = None

        if "AGREEMENT_REACHED:" in response:
            signal = "AGREEMENT_REACHED"
            try:
                option_part = response.split("AGREEMENT_REACHED:")[1].strip()
                agreed_option = option_part.split()[0].strip("{}")
            except (IndexError, ValueError):
                agreed_option = "B"  # Default
            ai_message = response.split("AGREEMENT_REACHED:")[0].strip()
            if not ai_message:
                ai_message = (
                    "Wonderful! Both parties have reached an agreement. "
                    "I will now prepare the settlement document for your review and signatures."
                )
            logger.info(f"Agreement reached on option: {agreed_option}")

        elif "ESCALATE_TO_ARBITRATION" in response:
            signal = "ESCALATE_TO_ARBITRATION"
            ai_message = response.split("ESCALATE_TO_ARBITRATION")[0].strip()
            if not ai_message:
                ai_message = (
                    "After careful facilitation, it appears that mediation alone "
                    "may not be sufficient for this dispute. I am now escalating this matter "
                    "to binding arbitration under the Arbitration & Conciliation Act, 1996. "
                    "An arbitration brief with case precedents will be prepared for the arbitrator."
                )
            logger.info("Mediation escalated to arbitration")

        else:
            ai_message = response
            # Check for escalation signals in user message
            escalation_keywords = [
                "court", "lawyer", "sue", "legal action", "refuse",
                "never", "impossible", "waste of time"
            ]
            if any(kw in user_message.lower() for kw in escalation_keywords):
                self.escalation_signals += 1
                logger.info(f"Escalation signal detected: {self.escalation_signals}/3")

        return {
            "ai_response": ai_message,
            "signal": signal,
            "agreed_option": agreed_option,
        }

    def get_opening_message(self) -> str:
        """Get the AI's opening message for the joint session"""
        return self.synthesis_data.get(
            "recommended_opening",
            "Welcome to this joint mediation session. I have reviewed both perspectives "
            "and prepared settlement options for your consideration. Let us work together "
            "to find a resolution that respects both parties' interests."
        )
