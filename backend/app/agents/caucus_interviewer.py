"""
Madhyastha — Agent 1: Caucus Interviewer
Private one-on-one AI interviewer for each party
Extracts: position, interest, min_acceptable, emotional_need
"""

import json
import re
import logging
from typing import Dict, Optional, List
from app.services.groq_service import groq_service
from app.prompts.mediator_prompts import CAUCUS_SYSTEM_PROMPT

logger = logging.getLogger("madhyastha.agent.caucus")


class CaucusInterviewer:
    """Private caucus session agent that interviews each party individually"""

    def __init__(self, dispute_context: dict):
        self.dispute_type = dispute_context.get("dispute_type", "other_civil")
        self.dispute_title = dispute_context.get("title", "Dispute")
        self.party_role = dispute_context.get("party_role", "party_a")
        self.party_name = dispute_context.get("party_name", "Party")
        self.language = dispute_context.get("language", "en")

        self.system_prompt = CAUCUS_SYSTEM_PROMPT.format(
            dispute_type=self.dispute_type,
            dispute_title=self.dispute_title,
            party_role=self.party_role,
            party_name=self.party_name,
            language=self.language,
        )

    async def chat(
        self,
        user_message: str,
        chat_history: Optional[List[Dict[str, str]]] = None,
    ) -> dict:
        """
        Process a message from the party and return AI response.
        Returns: {
            "ai_response": str,
            "statement_complete": bool,
            "extracted_statement": Optional[dict]
        }
        """
        response = await groq_service.chat(
            system_prompt=self.system_prompt,
            user_message=user_message,
            chat_history=chat_history,
            temperature=0.7,
            max_tokens=1024,
        )

        # Check if statement extraction is complete
        statement_complete = False
        extracted_statement = None

        if "STATEMENT_COMPLETE" in response:
            statement_complete = True
            try:
                # Extract JSON after STATEMENT_COMPLETE
                json_part = response.split("STATEMENT_COMPLETE")[1].strip()
                # Remove leading colon/whitespace
                json_part = json_part.lstrip(": \n")
                # Clean up - find the JSON object
                start = json_part.find("{")
                end = json_part.rfind("}") + 1
                if start != -1 and end > start:
                    raw_json = json_part[start:end]
                    # Fix common LLM issues:
                    # 1. Double braces {{ }} from prompt escaping
                    raw_json = raw_json.replace("{{", "{").replace("}}", "}")
                    # 2. Single quotes instead of double quotes
                    raw_json = raw_json.replace("'", '"')
                    # 3. Trailing commas before closing brace
                    import re
                    raw_json = re.sub(r',\s*}', '}', raw_json)
                    raw_json = re.sub(r',\s*]', ']', raw_json)

                    extracted_statement = json.loads(raw_json)
                    logger.info(f"Statement extracted for {self.party_name}: {extracted_statement}")

                # Get the AI message (before STATEMENT_COMPLETE)
                ai_message = response.split("STATEMENT_COMPLETE")[0].strip()
                if not ai_message:
                    ai_message = (
                        "Thank you for sharing all of this with me. I now have a clear "
                        "understanding of your perspective. Your statement has been recorded "
                        "and will be kept confidential. The mediation will proceed once both "
                        "parties have completed their sessions."
                    )
            except (json.JSONDecodeError, IndexError, ValueError) as e:
                logger.error(f"Failed to parse statement: {e}")
                # Try to extract fields manually as fallback
                try:
                    fallback = {}
                    for field in ["position", "interest", "min_acceptable", "emotional_need"]:
                        match = re.search(rf'"{field}"\s*:\s*"([^"]*)"', response)
                        if not match:
                            match = re.search(rf"'{field}'\s*:\s*'([^']*)'", response)
                        if match:
                            fallback[field] = match.group(1)
                    if len(fallback) >= 3:
                        extracted_statement = fallback
                        logger.info(f"Statement extracted via fallback for {self.party_name}: {extracted_statement}")
                except Exception:
                    pass
                ai_message = response.split("STATEMENT_COMPLETE")[0].strip() or response
        else:
            ai_message = response

        return {
            "ai_response": ai_message,
            "statement_complete": statement_complete,
            "extracted_statement": extracted_statement,
        }
