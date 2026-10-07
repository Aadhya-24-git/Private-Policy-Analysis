import re
from typing import Optional


def clean_model_scaffolding(text: Optional[str]) -> str:
    """
    Strips LLM reasoning and prompt scaffolding artifacts from model outputs,
    including Qwen reasoning tags (<think>), untrusted context echoes, Audit Rationale,
    Strict Compliance with Directives, Final Answer headers, Retrieved Context,
    System Instructions, Reasoning, and Thinking sections.
    """
    if not text:
        return ""

    cleaned = text.replace("\x00", "")

    # 1. Remove thinking blocks e.g. <think>...</think> (including unclosed tags)
    cleaned = re.sub(r"<think>[\s\S]*?(?:</think>|$)", "", cleaned, flags=re.IGNORECASE)

    # 2. Remove untrusted_policy_context blocks or leftover tags
    cleaned = re.sub(
        r"<untrusted_policy_context[^>]*>[\s\S]*?</untrusted_policy_context>",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(r"</?untrusted_policy_context[^>]*>", "", cleaned, flags=re.IGNORECASE)

    # 3. Remove user_question blocks or leftover tags
    cleaned = re.sub(r"<user_question[^>]*>[\s\S]*?</user_question>", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"</?user_question[^>]*>", "", cleaned, flags=re.IGNORECASE)

    # 4. Remove prompt echo prefixes and instructional fragments
    cleaned = re.sub(
        r"(?:^|\n)\s*Audit Analysis\s*&\s*Grounded Answer(?:\s*\([^)]*\))?:?\s*",
        "\n",
        cleaned,
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(
        r"(?:^|\n)\s*(?:Please answer the question according to|Required Response Format:)[^\n]*\n*",
        "\n",
        cleaned,
        flags=re.IGNORECASE,
    )

    # 5. Strip internal scaffolding headers and their content if present
    # Targets: Audit Rationale, Strict Compliance with Directives, Retrieved Context,
    # System Instructions, Reasoning, Thinking, Internal Rationale
    scaffolding_headers = [
        r"Audit Rationale",
        r"Strict Compliance with Directives",
        r"Retrieved Context",
        r"System Instructions",
        r"Reasoning",
        r"Thinking",
        r"Internal Rationale",
    ]
    for header in scaffolding_headers:
        cleaned = re.sub(
            rf"(?:^|\n)\s*(?:#{1,6}\s*)?(?:\*\*|__)?\s*{header}\s*:?\s*(?:\*\*|__)?\s*:?[^\n]*\n*",
            "\n",
            cleaned,
            flags=re.IGNORECASE,
        )

    # 6. If "Answer:" appears after preliminary chain-of-thought monologue,
    # extract strictly from "Answer:"
    answer_match = re.search(
        r"(?:^|\n)\s*(?:#{1,6}\s*)?(?:\*\*|__)?\s*Answer\s*:?\s*(?:\*\*|__)?\s*:?\s*",
        cleaned,
        flags=re.IGNORECASE,
    )
    if answer_match:
        # Check if there is significant conversational preamble before Answer:
        preamble = cleaned[:answer_match.start()].strip()
        # If the text preceding Answer: looks like reasoning, trim it
        if preamble:
            cleaned = "Answer:\n" + cleaned[answer_match.end():].lstrip()
    elif not cleaned.strip().lower().startswith("answer:"):
        # If model started directly with answer sentences following an assistant prefill
        if re.search(r"\bWhat this means:\b", cleaned, flags=re.IGNORECASE):
            cleaned = "Answer:\n" + cleaned.lstrip()

    # 7. Extract content after "Final Answer" section if preceded by scaffolding
    final_answer_match = re.search(
        r"(?:^|\n)\s*(?:#{1,6}\s*)?(?:\*\*|__)?\s*Final Answer\s*:?\s*(?:\*\*|__)?\s*:?\s*",
        cleaned,
        flags=re.IGNORECASE,
    )
    if final_answer_match:
        post_final = cleaned[final_answer_match.end():].strip()
        if post_final:
            cleaned = post_final

    # 8. Strip any duplicate repeated sections after the primary "Source:" block
    # (e.g. if the model started repeating prompt context or looping)
    source_match = re.search(
        r"((?:^|\n)\s*(?:#{1,6}\s*)?(?:\*\*|__)?\s*Source\s*:?\s*(?:\*\*|__)?\s*:[^\n]+)",
        cleaned,
        flags=re.IGNORECASE,
    )
    if source_match:
        end_pos = source_match.end()
        # Check if text after source contains repeated prompt/looping artifacts
        trailing_text = cleaned[end_pos:]
        if re.search(r"(?:user\b|context:|answer:|<think>|<untrusted_policy_context>)", trailing_text, flags=re.IGNORECASE):
            cleaned = cleaned[:end_pos].strip()

    # 9. Clean redundant blank lines
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)

    return cleaned.strip()
