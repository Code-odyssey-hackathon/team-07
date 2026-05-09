"""
Madhyastha — Groq LLM Service
Wrapper for Groq API chat completions
"""

import json
import logging
from typing import Optional, List, Dict, Any
from app.core.config import settings

logger = logging.getLogger("madhyastha.groq")

# Try to import groq, fall back to mock if not available
try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False
    logger.warning("Groq package not installed. Using mock responses.")


class GroqService:
    """Service for interacting with Groq LLM API"""

    def __init__(self):
        self.client = None
        self.model = settings.GROQ_MODEL
        self.fallback_model = "llama-3.1-8b-instant"  # Higher rate limits, used when primary is rate-limited

        if GROQ_AVAILABLE and settings.GROQ_API_KEY:
            try:
                self.client = Groq(api_key=settings.GROQ_API_KEY)
                logger.info(f"Groq client initialized with model: {self.model}")
            except Exception as e:
                logger.error(f"Failed to initialize Groq client: {e}")
        else:
            logger.warning("Groq API key not configured. Using mock responses.")

    async def chat(
        self,
        system_prompt: str,
        user_message: str,
        chat_history: Optional[List[Dict[str, str]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        """Send a chat completion request to Groq"""
        messages = [{"role": "system", "content": system_prompt}]

        # Add chat history if provided
        if chat_history:
            for msg in chat_history:
                messages.append({
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", ""),
                })

        # Add current user message
        messages.append({"role": "user", "content": user_message})

        if self.client:
            # Try primary model first, fall back to smaller model on rate limit
            for model in [self.model, self.fallback_model]:
                try:
                    response = self.client.chat.completions.create(
                        model=model,
                        messages=messages,
                        temperature=temperature,
                        max_tokens=max_tokens,
                    )
                    if model != self.model:
                        logger.info(f"Used fallback model: {model}")
                    return response.choices[0].message.content
                except Exception as e:
                    error_str = str(e)
                    if "429" in error_str or "rate_limit" in error_str:
                        logger.warning(f"Rate limited on {model}, trying fallback...")
                        continue
                    else:
                        logger.error(f"Groq API error on {model}: {e}")
                        break
            # All models failed
            logger.error("All models rate limited or failed. Using mock response.")
            return self._mock_response(system_prompt, user_message)
        else:
            return self._mock_response(system_prompt, user_message)

    async def chat_json(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> Dict[str, Any]:
        """Send a chat request expecting JSON response"""
        response_text = await self.chat(
            system_prompt=system_prompt,
            user_message=user_message,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        # Try to extract JSON from the response
        try:
            # Look for JSON block in response
            if "```json" in response_text:
                json_str = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                json_str = response_text.split("```")[1].split("```")[0].strip()
            elif response_text.strip().startswith("{"):
                json_str = response_text.strip()
            else:
                # Try to find JSON object in the text
                start = response_text.find("{")
                end = response_text.rfind("}") + 1
                if start != -1 and end > start:
                    json_str = response_text[start:end]
                else:
                    return {"raw_response": response_text}

            return json.loads(json_str)
        except json.JSONDecodeError:
            logger.error(f"Failed to parse JSON from Groq response: {response_text[:200]}")
            return {"raw_response": response_text}

    def _mock_response(self, system_prompt: str, user_message: str) -> str:
        """Generate a mock response when Groq is not available"""
        if "caucus" in system_prompt.lower() or "private" in system_prompt.lower():
            return self._mock_caucus_response(user_message)
        elif "synthesis" in system_prompt.lower():
            return self._mock_synthesis_response()
        elif "joint" in system_prompt.lower() and "mediator" in system_prompt.lower():
            return self._mock_joint_response(user_message)
        elif "agreement" in system_prompt.lower() and "drafter" in system_prompt.lower():
            return self._mock_agreement_response()
        elif "arbitration" in system_prompt.lower() and "brief" in system_prompt.lower():
            return self._mock_brief_response()
        else:
            return "I understand your concern. Could you tell me more about what happened and what resolution you're looking for?"

    def _mock_caucus_response(self, user_message: str) -> str:
        """Mock caucus interviewer responses"""
        keywords = user_message.lower()
        if any(w in keywords for w in ["want", "demand", "claim", "need", "pay", "return"]):
            return (
                "Thank you for sharing that. I understand this is important to you. "
                "Help me understand — what is the underlying reason this matters so much? "
                "What would resolving this mean for you personally?"
            )
        elif any(w in keywords for w in ["fair", "respect", "principle", "wrong"]):
            return (
                "I hear you — the sense of fairness is clearly very important here. "
                "If we could find a resolution, what would be the minimum outcome "
                "you could accept while still feeling the situation was handled fairly?"
            )
        else:
            return (
                "Thank you for sharing your perspective. I want to make sure I understand fully. "
                "Could you tell me: what specific outcome are you hoping for from this mediation? "
                "What would a good resolution look like to you?"
            )

    def _mock_synthesis_response(self) -> str:
        """Mock synthesis analysis"""
        return json.dumps({
            "conflict_zones": [
                "Disagreement on the total amount to be settled",
                "Timeline for payment/resolution differs"
            ],
            "overlap_zones": [
                "Both parties acknowledge the underlying relationship",
                "Both prefer resolution over court proceedings"
            ],
            "settlement_options": [
                {
                    "option_id": "A",
                    "title": "Full Settlement with Extended Timeline",
                    "terms": "Full claimed amount paid over 24 months in equal installments",
                    "timeline": "24 months from agreement date",
                    "enforcement": "Post-dated cheques or standing instruction",
                    "favors": "party_a",
                    "precedent_ref": "Similar to outcome in Ramesh v. Suresh (2022) — Lok Adalat settlement"
                },
                {
                    "option_id": "B",
                    "title": "Negotiated Lump Sum Settlement",
                    "terms": "70% of claimed amount as one-time payment within 30 days",
                    "timeline": "30 days from agreement",
                    "enforcement": "Bank guarantee or escrow arrangement",
                    "favors": "neutral",
                    "precedent_ref": "Based on precedent in Consumer Forum Case #CF/2021/4521"
                },
                {
                    "option_id": "C",
                    "title": "Partial Payment + Asset/Service Compensation",
                    "terms": "50% cash payment + transfer of equivalent value in assets/services",
                    "timeline": "60 days for cash, 90 days for asset transfer",
                    "enforcement": "Registered transfer deed + payment receipt",
                    "favors": "party_b",
                    "precedent_ref": "Similar arrangement in Property Dispute #PD/2023/1892"
                }
            ],
            "recommended_opening": (
                "Welcome to this joint mediation session. Both of you have shown "
                "courage and good faith by choosing to resolve this matter through mediation "
                "rather than litigation. I have carefully reviewed the situation and prepared "
                "three possible settlement options for your consideration. Let us discuss each "
                "one and find the path that works best for both of you."
            )
        })

    def _mock_joint_response(self, user_message: str) -> str:
        """Mock joint mediator responses"""
        return (
            "Thank you for that perspective. I want to ensure both parties feel heard. "
            "Looking at the settlement options before us, Option B seems to balance "
            "both parties' core interests. Would both of you like to discuss the specific "
            "terms of this option in more detail?"
        )

    def _mock_agreement_response(self) -> str:
        """Mock agreement drafter"""
        return json.dumps({
            "title": "Mediation Settlement Agreement",
            "date": "2025-01-15",
            "reference_number": "MSA/2025/0001",
            "legal_basis": "Section 22, Mediation Act, 2023",
            "sections": [
                {"heading": "Parties", "content": "This agreement is between the parties involved in the dispute."},
                {"heading": "Dispute Description", "content": "The parties were in a civil dispute regarding the matter described in the mediation proceedings."},
                {"heading": "Agreed Terms", "content": "The parties have agreed to the settlement terms as negotiated during the mediation session."},
                {"heading": "Payment Schedule", "content": "Payment shall be made as per the agreed timeline."},
                {"heading": "Default Clause", "content": "In the event of non-compliance, the aggrieved party may approach the appropriate court for enforcement."},
                {"heading": "Signatures", "content": "Signed by both parties and attested by the AI Mediation System."},
                {"heading": "Legal Citation", "content": "This agreement is executed under Section 22 of the Mediation Act, 2023."}
            ],
            "enforcement_note": "This agreement is binding and enforceable as per Section 22 of the Mediation Act, 2023."
        })

    def _mock_brief_response(self) -> str:
        """Mock arbitration brief"""
        return json.dumps({
            "case_id": "ARB/2025/0001",
            "prepared_date": "2025-01-15",
            "sections": [
                {"number": 1, "heading": "Case Summary", "content": "Civil dispute requiring arbitration after mediation failure."},
                {"number": 2, "heading": "Timeline", "content": "Dispute registered and mediation attempted."},
                {"number": 3, "heading": "Party A Position", "content": "Party A's claims and evidence."},
                {"number": 4, "heading": "Party B Position", "content": "Party B's claims and evidence."},
                {"number": 5, "heading": "Mediation History", "content": "AI mediation was attempted but parties could not reach agreement."},
                {"number": 6, "heading": "Evidence Index", "content": "All submitted documents and statements."},
                {"number": 7, "heading": "Relevant Precedents", "content": "Applicable Indian legal precedents."},
                {"number": 8, "heading": "Suggested Award Options", "content": "Three possible award structures."},
                {"number": 9, "heading": "Consent Status", "content": "Both parties have consented to binding arbitration."}
            ],
            "legal_basis": "Arbitration and Conciliation Act, 1996",
            "suggested_awards": [
                {"option": "A", "type": "full_payment", "terms": "Full amount as claimed", "legal_basis": "Section 31", "precedent": "Standard award precedent"}
            ]
        })


# Global instance
groq_service = GroqService()
