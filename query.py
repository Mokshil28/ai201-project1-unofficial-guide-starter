"""
Milestone 5 — grounded answer generation.

Pipeline (matches planning.md):
    query -> retrieve(top-k from ChromaDB) -> Groq llama-3.3-70b-versatile
          -> answer grounded in retrieved chunks ONLY + source citations

Usage:
    python query.py "Is there a party scene at UNC Charlotte?"

Grounding is enforced two ways:
  1. A strict system prompt: answer only from the provided context, and say
     "I don't have enough information on that." when the context doesn't cover it.
  2. Source attribution is appended programmatically from the retrieved chunks'
     metadata, so citations are guaranteed rather than left to the model.
"""

import os
import sys

from dotenv import load_dotenv
from groq import Groq

from embed import retrieve, TOP_K

load_dotenv()

GROQ_MODEL = "llama-3.3-70b-versatile"   # from planning.md
# If the closest chunk is farther than this cosine distance, treat the question
# as out-of-scope and refuse rather than forcing an answer from weak context.
MAX_DISTANCE = 0.75

SYSTEM_PROMPT = (
    "You are The Unofficial Guide to UNC Charlotte. You answer questions using "
    "ONLY the student-written context provided below. Follow these rules strictly:\n"
    "1. Base every statement on the provided context. Do NOT use outside knowledge.\n"
    "2. If the context does not contain enough information to answer, reply exactly: "
    "\"I don't have enough information on that.\"\n"
    "3. Do not invent facts, names, or numbers that are not in the context.\n"
    "4. Keep answers concise and reflect that these are subjective student opinions "
    "(e.g., \"Students say...\", \"Several commenters mention...\")."
)


def _client():
    key = os.getenv("GROQ_API_KEY")
    if not key or key == "your_key_here":
        raise SystemExit(
            "GROQ_API_KEY is not set. Copy .env.example to .env and paste your "
            "Groq key (get one free at https://console.groq.com)."
        )
    return Groq(api_key=key)


def _format_context(hits):
    """Number each retrieved chunk and label it with its source document."""
    blocks = []
    for i, h in enumerate(hits, 1):
        blocks.append(f"[{i}] (source: {h['source']})\n{h['text']}")
    return "\n\n".join(blocks)


def ask(question, k=TOP_K):
    """Retrieve context and generate a grounded answer with source citations.

    Returns {"answer": str, "sources": [filenames]}.
    """
    hits = retrieve(question, k=k)

    # Out-of-scope guard: if nothing is even loosely relevant, refuse up front.
    if not hits or hits[0]["distance"] > MAX_DISTANCE:
        return {"answer": "I don't have enough information on that.", "sources": []}

    context = _format_context(hits)
    user_msg = (
        f"Context (student posts about UNC Charlotte):\n\n{context}\n\n"
        f"Question: {question}\n\n"
        "Answer using only the context above."
    )

    resp = _client().chat.completions.create(
        model=GROQ_MODEL,
        temperature=0.2,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ],
    )
    answer = resp.choices[0].message.content.strip()

    # Programmatic source attribution: unique sources, preserving rank order.
    # Omit sources when the model declined (nothing was actually used).
    sources = []
    if "i don't have enough information" not in answer.lower():
        for h in hits:
            if h["source"] not in sources:
                sources.append(h["source"])

    return {"answer": answer, "sources": sources}


if __name__ == "__main__":
    q = " ".join(sys.argv[1:]) or "Is there a party scene at UNC Charlotte?"
    result = ask(q)
    print(f"\nQ: {q}\n")
    print(f"A: {result['answer']}\n")
    if result["sources"]:
        print("Sources:")
        for s in result["sources"]:
            print(f"  - {s}")
    else:
        print("Sources: (none — question not covered by the documents)")
