import logging
from typing import Optional
from app.llm.base import BaseLLMClient
from app.llm.provider import get_llm_client

logger = logging.getLogger(__name__)

COMPARISON_SYSTEM_PROMPT = """You are the AI-Powered Fine Print Auditor comparison engine.
Your sole responsibility is to explain the concrete factual differences between an OLD clause and an updated NEW clause.

STRICT INSTRUCTIONS:
1. Ground your explanation EXCLUSIVELY on the provided Old Clause and New Clause texts.
2. Do NOT invent, assume, extrapolate, or hallucinate changes that are not present.
3. Clearly and neutrally describe what terms were added, deleted, or revised in 1 to 2 concise sentences.
4. Distinguish factual textual changes from legal implications.
5. Use professional, objective language with zero legal conclusions."""


def explain_clause_modification(
    old_text: str,
    new_text: str,
    llm_client: Optional[BaseLLMClient] = None,
) -> str:
    """
    Generate an objective, neutral explanation of what factually changed between
    an old clause and a new clause. Falls back gracefully if LLM is unavailable.
    """
    client = llm_client or get_llm_client()

    user_prompt = (
        f"Old Clause Version:\n\"{old_text.strip()}\"\n\n"
        f"New Clause Version:\n\"{new_text.strip()}\"\n\n"
        "Concise Factual Explanation of Change:"
    )

    try:
        raw_res = client.generate(prompt=user_prompt, system_prompt=COMPARISON_SYSTEM_PROMPT)
        cleaned = raw_res.strip() if raw_res else ""
        if cleaned:
            return cleaned
    except Exception as e:
        logger.warning(f"LLM explanation generation skipped/failed: {e}")

    # Deterministic fallback explanation
    len_diff = len(new_text) - len(old_text)
    if len_diff > 0:
        return f"Clause text was expanded by approximately {len_diff} characters with revised terms."
    elif len_diff < 0:
        return f"Clause text was condensed by approximately {abs(len_diff)} characters with revised terms."
    return "Clause wording and stipulations were updated from the previous version."


def explain_added_clause(clause_text: str) -> str:
    return "Newly introduced clause establishing provisions not present in the previous policy version."


def explain_removed_clause(clause_text: str) -> str:
    return "Clause from the previous policy version was excised from the updated agreement."
