"""
Madhyastha — Bhashini Translation Service
Indian Government multilingual translation API
"""
import logging
from typing import Optional
from app.core.config import settings

logger = logging.getLogger("madhyastha.bhashini")

LANG_MAP = {
    "hi": "Hindi", "kn": "Kannada", "ta": "Tamil", "te": "Telugu",
    "mr": "Marathi", "bn": "Bengali", "gu": "Gujarati",
    "pa": "Punjabi", "ml": "Malayalam", "en": "English"
}


async def translate(text: str, source_lang: str = "en", target_lang: str = "hi") -> str:
    """Translate text using Bhashini ULCA API"""
    if source_lang == target_lang:
        return text
    if not settings.BHASHINI_API_KEY:
        logger.info(f"[MOCK TRANSLATE] {source_lang}→{target_lang}: {text[:50]}...")
        return text  # Return original text as fallback
    try:
        import httpx
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://meity-auth.ulcacontrib.org/ulca/apis/v0/model/compute",
                headers={"ulcaApiKey": settings.BHASHINI_API_KEY,
                         "userID": settings.BHASHINI_USER_ID},
                json={"pipelineTasks": [{"taskType": "translation",
                      "config": {"language": {"sourceLanguage": source_lang,
                                              "targetLanguage": target_lang}}}],
                      "inputData": {"input": [{"source": text}]}}
            )
            if resp.status_code == 200:
                data = resp.json()
                return data["pipelineResponse"][0]["output"][0]["target"]
    except Exception as e:
        logger.error(f"Translation failed: {e}")
    return text
