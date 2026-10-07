import sys
import os

sys.path.insert(0, os.path.realpath(os.path.join(os.path.dirname(__file__), "..")))

from app.llm.embeddings import get_embedding_provider
from app.llm.provider import get_llm_client
from app.rag.qa_service import AUDITOR_SYSTEM_PROMPT

def main():
    print("==================================================================")
    print("LIVE VERIFICATION: OLLAMA + QWEN INTEGRATION")
    print("==================================================================")

    # 1. Embedding Model Verification
    print("\n[1/2] Testing Live Ollama Embeddings (qwen3-embedding:0.6b)...")
    emb = get_embedding_provider()
    sample_text = "This contract automatically renews for additional 1-year terms unless cancelled 30 days prior."
    vec = emb.embed_text(sample_text)
    print(f"Provider: {emb.__class__.__name__}")
    print(f"Model: {emb.model}")
    print(f"Output Vector Dimension: {len(vec)}")
    print(f"First 5 Vector Components: {vec[:5]}")
    assert len(vec) == 1024, f"Expected 1024 dimensions, got {len(vec)}"
    print("--> Embedding Generation: SUCCESS (1024 dimensions verified)")

    # 2. Chat Model Verification (Qwen3:4b)
    print("\n[2/2] Testing Live Ollama Chat Generation (qwen3:4b)...")
    llm = get_llm_client()
    print(f"Provider: {llm.__class__.__name__}")
    print(f"Model: {llm.model}")

    policy_clause = (
        "[Clause #1, Section: Cancellation & Renewal, Page 4]\n"
        "Subscriptions automatically renew for successive 12-month periods unless notice of termination "
        "is delivered at least thirty (30) days prior to the expiration date. An administrative cancellation "
        "fee of $75.00 shall apply to all early terminations."
    )
    user_question = "What is the cancellation fee and how many days in advance must I notify to avoid renewal?"

    prompt = (
        f"<untrusted_policy_context document='Master Services Agreement.pdf'>\n"
        f"{policy_clause}\n"
        f"</untrusted_policy_context>\n\n"
        f"<user_question>\n"
        f"{user_question}\n"
        f"</user_question>\n\n"
        f"Audit Analysis & Grounded Answer (relying strictly on the <untrusted_policy_context> evidence above):"
    )

    answer = llm.generate(prompt=prompt, system_prompt=AUDITOR_SYSTEM_PROMPT)
    print(f"\nModel Answer:\n{answer}\n")
    assert "$75" in answer or "75" in answer, "Expected cancellation fee ($75) in answer"
    assert "30" in answer, "Expected 30 days notice in answer"
    print("--> Grounded Q&A Generation: SUCCESS")
    print("==================================================================")
    print("ALL LIVE OLLAMA + QWEN CAPABILITIES SUCCESSFULLY VERIFIED!")
    print("==================================================================")

if __name__ == "__main__":
    main()
