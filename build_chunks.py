"""
Milestone 3 — Document ingestion + chunking pipeline.

Pipeline (matches planning.md):
    data/*.txt  ->  load  ->  clean  ->  chunk (500 chars, 100 overlap)  ->  chunks.json

Run:
    python build_chunks.py

Output:
    raw_documents.json  — each document's cleaned full text (for inspection)
    chunks.json         — list of {id, source, text} chunks, ready for Milestone 4 embedding
"""

import html
import json
import re
import sys
from pathlib import Path

# Windows consoles default to cp1252 and crash when printing emoji / unusual
# Unicode found in Reddit text. Force UTF-8 output so inspection never fails.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass

# --- Config (from planning.md "Chunking Strategy") -------------------------
DATA_DIR = Path(__file__).parent / "data"
CHUNK_SIZE = 500        # characters
CHUNK_OVERLAP = 100     # characters
MIN_CHUNK_LEN = 50      # drop near-empty fragments below this length

# Filenames in data/ have no extension on a couple of files, so we load
# everything that isn't hidden rather than filtering by ".txt".
def list_source_files():
    return sorted(
        p for p in DATA_DIR.iterdir()
        if p.is_file() and not p.name.startswith(".")
    )


# --- Stage 1: Load ---------------------------------------------------------
def load_documents():
    """Read every source file in data/ into {source_name: raw_text}."""
    docs = {}
    for path in list_source_files():
        text = path.read_text(encoding="utf-8", errors="replace")
        docs[path.name] = text
    return docs


# --- Stage 2: Clean --------------------------------------------------------
# Whole-line patterns that are pure Reddit chrome and carry no real content.
# Matched case-insensitively against a stripped line.
BOILERPLATE_LINE_PATTERNS = [
    r"^(reply|share|report|save|award|follow|give award)$",
    r"^read more$",
    r"^(see more|view more comments?|load more comments?|view all comments)$",
    r"^continue this thread.*$",
    r"^\d+\s*(points?|upvotes?|comments?|awards?)$",
    r"^(upvote|downvote)$",
    r"^level \d+$",                              # old-reddit comment depth markers
    r"^edit\s*\d*\s*:?$",
    r"^edited\b.*ago\.?$",                       # "Edited 3mo ago"
    r"^(moderator|mod)\b.*$",                     # "moderator emeritus" flair
    r"^[\W_]+$",                                 # separator-only lines (middots, dashes)
    r"^more replies?$",
    r"^\[(deleted|removed)\]$",                  # deleted/removed comment markers
    r"^OP$",                                     # original-poster tag
    r"^u/\S+\s*(avatar)?$",                      # "u/Name" / "u/Name avatar"
    r".*\bavatar$",                              # "Name avatar" lines
    r"^\d+$",                                    # standalone vote-count numbers
    r"^[\d.]+k$",                                # "1.2k" vote counts
    r"^(former|current|prospective)?\s*(student|alumni|alum|faculty|staff|professor|graduate)\b.*$",
    r"^(undergrad|undergraduate|grad)\b.*$",
    # Reddit page chrome / nav that gets copied above the comments
    r"^go to comments$",
    r"^join the conversation$",
    r"^sort by:?$",
    r"^best$",
    r"^(search comments|expand comment search)$",
    r"^comments?\s*section$",
    r"^(single comment thread|view all comments|add a comment)$",
    # Promoted-ad chrome
    r"^promoted$",
    r"^(sign up|shop now|learn more|download|install|get offer)$",
    r"^thumbnail image:.*$",
    r"^\S+\.(com|net|org|io|co|gov|edu|app|ai)$",   # bare domain lines
]
BOILERPLATE_RE = [re.compile(p, re.IGNORECASE) for p in BOILERPLATE_LINE_PATTERNS]

# A line that is just a relative timestamp: "4y ago", "3mo ago", "8 months ago".
TIMESTAMP_RE = re.compile(
    r"^\s*\d+\s*"
    r"(s|sec|secs|seconds?|m|min|mins|minutes?|h|hr|hrs|hours?|d|days?|"
    r"w|wk|wks|weeks?|mo|mos|months?|y|yr|yrs|years?)\s*ago\.?\s*$",
    re.IGNORECASE,
)

# A line that looks like a bare Reddit username (single token, no spaces).
USERNAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_\-]{2,30}$")

# Markers that close a "Promoted" ad block (domain or thumbnail caption line).
PROMOTED_RE = re.compile(r"^promoted$", re.IGNORECASE)
AD_END_RE = re.compile(r"^(\S+\.(com|net|org|io|co|gov|edu|app|ai)|thumbnail image:.*)$",
                       re.IGNORECASE)

# Inline junk to strip from anywhere within a line.
HTML_TAG_RE = re.compile(r"<[^>]+>")
URL_RE = re.compile(r"https?://\S+")

# Smart punctuation -> ASCII, so chunks are clean for embedding and display.
PUNCT_MAP = {
    "’": "'", "‘": "'", "“": '"', "”": '"',
    "–": "-", "—": "-", "…": "...", " ": " ",
}


def _is_username_line(stripped, lines, i):
    """A bare token is treated as a username only when a timestamp or middot
    follows soon after (the Reddit username -> middot -> 'X ago' structure),
    so we don't strip legitimate one-word content lines."""
    if " " in stripped or not USERNAME_RE.match(stripped):
        return False
    for j in range(i + 1, min(i + 4, len(lines))):
        nxt = lines[j].strip()
        if not nxt:
            continue
        return bool(TIMESTAMP_RE.match(nxt) or re.match(r"^[\W_]+$", nxt))
    return False


def clean_text(raw: str) -> str:
    """Strip HTML, entities, URLs, and Reddit boilerplate; normalize whitespace."""
    text = HTML_TAG_RE.sub("", raw)        # remove HTML tags
    text = html.unescape(text)             # &amp; &#39; &nbsp; -> & ' (space)
    text = text.replace(" ", " ")
    for bad, good in PUNCT_MAP.items():     # smart quotes/dashes/nbsp -> ASCII
        text = text.replace(bad, good)

    raw_lines = text.splitlines()
    kept = []
    skipping_ad = 0  # >0 while inside a "Promoted" ad block (free-text copy)
    for i, line in enumerate(raw_lines):
        stripped = URL_RE.sub("", line).strip()
        if not stripped:
            continue
        # Skip the free-text body of a Promoted ad until its domain/thumbnail
        # line, which line patterns alone can't match. Cap at 20 lines so a
        # missing end-marker can't swallow real comments.
        if skipping_ad:
            skipping_ad -= 1
            if AD_END_RE.match(stripped) or skipping_ad == 0:
                skipping_ad = 0
            continue
        if PROMOTED_RE.match(stripped):
            skipping_ad = 20
            continue
        if TIMESTAMP_RE.match(stripped):
            continue
        if any(rx.match(stripped) for rx in BOILERPLATE_RE):
            continue
        if _is_username_line(stripped, raw_lines, i):
            continue
        kept.append(stripped)

    text = "\n".join(kept)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()


# --- Stage 3: Chunk --------------------------------------------------------
def chunk_text(text: str, size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    """
    Sliding-window chunker: ~`size` chars with `overlap` chars of carry-over.

    To avoid the "Professor Smith's exams are heavily" fragment problem, each
    window's end is snapped back to the nearest sentence end (. ! ? newline)
    or whitespace so chunks don't cut mid-word. Chunk size is therefore a
    target, not a hard cut — which is why chunk lengths vary slightly.
    """
    text = text.strip()
    if not text:
        return []

    chunks = []
    start = 0
    n = len(text)
    while start < n:
        # Snap the start forward to a word boundary so chunks don't begin
        # mid-word (the overlap tail otherwise lands inside a word).
        if start > 0:
            nxt_space = text.find(" ", start)
            if 0 <= nxt_space - start <= overlap:
                start = nxt_space + 1

        end = min(start + size, n)

        if end < n:
            window = text[start:end]
            # Prefer a sentence boundary in the back half of the window.
            boundary = max(window.rfind(". "), window.rfind("! "),
                           window.rfind("? "), window.rfind("\n"))
            if boundary > size // 2:
                end = start + boundary + 1
            else:
                space = window.rfind(" ")
                if space > size // 2:
                    end = start + space

        chunk = text[start:end].strip()
        if len(chunk) >= MIN_CHUNK_LEN:
            chunks.append(chunk)

        if end >= n:
            break
        start = max(end - overlap, start + 1)  # step forward with overlap

    return chunks


# --- Driver ----------------------------------------------------------------
def build():
    docs = load_documents()
    if not docs:
        print(f"No files found in {DATA_DIR}. Add your documents and re-run.")
        return

    raw_out = {}
    all_chunks = []
    empty_sources = []

    for source, raw in docs.items():
        cleaned = clean_text(raw)
        raw_out[source] = cleaned
        if not cleaned:
            empty_sources.append(source)
            continue
        for chunk in chunk_text(cleaned):
            all_chunks.append({
                "id": f"{source}::chunk_{len([c for c in all_chunks if c['source'] == source])}",
                "source": source,        # metadata: which document this came from
                "text": chunk,
            })

    (Path(__file__).parent / "raw_documents.json").write_text(
        json.dumps(raw_out, indent=2, ensure_ascii=False), encoding="utf-8")
    (Path(__file__).parent / "chunks.json").write_text(
        json.dumps(all_chunks, indent=2, ensure_ascii=False), encoding="utf-8")

    # --- Checkpoint output -------------------------------------------------
    print(f"Loaded {len(docs)} files from {DATA_DIR}")
    if empty_sources:
        print(f"\n  WARNING: {len(empty_sources)} file(s) are empty after cleaning "
              f"(or were empty to begin with):")
        for s in empty_sources:
            print(f"    - {s}")

    print(f"\nTotal chunks: {len(all_chunks)}")
    if all_chunks:
        lengths = [len(c["text"]) for c in all_chunks]
        print(f"Chunk length — min {min(lengths)}, max {max(lengths)}, "
              f"avg {sum(lengths)//len(lengths)} chars")

        print("\n--- 5 sample chunks (inspect these!) ---")
        import random
        for c in random.sample(all_chunks, min(5, len(all_chunks))):
            print(f"\n[{c['id']}]  ({len(c['text'])} chars)")
            print(c["text"])
            print("-" * 60)
    else:
        print("\nNo chunks produced. Your data files have no content yet — "
              "paste the Reddit thread text into data/*.txt and re-run.")


if __name__ == "__main__":
    build()
