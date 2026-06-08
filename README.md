# The Unofficial Guide — Project 1

A Retrieval-Augmented Generation (RAG) system that answers plain-language
questions about student life at UNC Charlotte using real student posts, with
source citations on every answer.

**Run it:**
```bash
pip install -r requirements.txt
python build_chunks.py     # load + clean + chunk documents -> chunks.json
python embed.py            # embed chunks into ChromaDB + test retrieval
python app.py              # launch the Gradio interface at http://localhost:7860
```
(Set your Groq API key in `.env` first — copy `.env.example` to `.env`.)

---

## Domain

My domain is **student experiences at UNC Charlotte** — housing, social life,
financial aid, campus culture, and computer-science student experiences.

This knowledge is valuable because official university pages publish policies
and marketing copy, but prospective and current students need the honest,
lived-experience perspective that only gets shared on Reddit and in student
communities — what a dorm is *actually* like, whether the campus is "dead" on
weekends, how the financial-aid process really goes. That candid information is
scattered across many threads and is hard to search directly.

---

## Document Sources

Ten Reddit threads from r/UNCCharlotte, collected manually (Reddit is
JavaScript-rendered and resists scraping) and saved as plain `.txt` files in
[`data/`](data/).

| # | Source | Type | File |
|---|--------|------|------|
| 1 | "What's something you wish you knew about UNCC before attending?" | Reddit thread | data/About_UNCC.txt |
| 2 | "What's Pine Hall Like?" | Reddit thread | data/PineHall.txt |
| 3 | "Financial Aid" | Reddit thread | data/FinancialData.txt |
| 4 | "oak hall" | Reddit thread | data/oakHall.txt |
| 5 | "Student Life at UNCC?" | Reddit thread | data/StudentLIife.txt |
| 6 | "Pros and Cons of UNCC?" | Reddit thread | data/ProsConsUNCC.txt |
| 7 | "How is uncc?" | Reddit thread | data/ComaprngUNCC.txt |
| 8 | "Chapel Hill or UNCC For Computer Science?" | Reddit thread | data/ChapelHillCSvsUNCC.txt |
| 9 | "Is there a party scene at UNCC?" | Reddit thread | data/PartyUNCC.txt |
| 10 | "How is the social life at UNCC? Is it really dead on the weekends?" | Reddit thread | data/PartyLifeUNCC.txt |

Source URLs are listed in [planning.md](planning.md).

---

## Chunking Strategy

Implemented in [`build_chunks.py`](build_chunks.py).

**Chunk size:** 500 characters (target)
**Overlap:** 100 characters

**Preprocessing before chunking:** Reddit posts are dense with non-content
"chrome." Each document is cleaned to remove: HTML tags, HTML entities
(`&amp;`, `&#39;`, `&nbsp;`), URLs, usernames, relative timestamps (`4y ago`,
`3mo ago`), standalone vote-count numbers, `OP` tags, `u/...avatar` lines, role
flair (`Alumni`, `moderator emeritus`), deleted/removed markers, "Archived post"
notices, page navigation (`Go to comments`, `Sort by`, `Comments Section`), and
**Promoted ad blocks** (including the free-text ad copy between the `Promoted`
marker and the advertiser's domain). Smart quotes and dashes are normalized to
ASCII so chunks embed and display cleanly.

**Why these choices fit my documents:** The corpus is short, opinion-based
Reddit comments. 500 characters is large enough to hold a complete student
thought (a full opinion about a dorm, a pros-and-cons list) but small enough
that a specific query matches precisely instead of being diluted across
unrelated topics. The 100-character overlap keeps an opinion that straddles a
boundary retrievable from either chunk. Rather than cutting mechanically at
exactly 500 characters, the chunker **snaps each boundary to the nearest
sentence or word break**, so chunks don't start or end mid-word — that is why
chunk lengths vary (≈167–499 characters) instead of being uniform.

**Final chunk count:** **143 chunks** across the 10 documents.

---

## Sample Chunks

Five representative chunks, each labeled with its source document:

**1 — PineHall.txt**
> friend of mine stayed there my sophomore year so I went over there a lot to
> work on projects, Compared to Belk or Martin which were the dorms I stayed in
> 3 of the 4 years, it's smaller, rooms just aren't as big or tall. The building
> layout was a little weird, with a central staircase per hallway with each half
> story landing having 2 rooms.

**2 — FinancialData.txt**
> Financial Aid. I'm an incoming transfer student, and didn't hear anything
> about any merit scholarships. I know I won't get anything from fafsa, but when
> i looked at the online uncc scholarship portal it didn't show up anything (and
> I assume it's because I don't have a uncc gpa yet) what have other people who
> needed aid done?

**3 — PartyLifeUNCC.txt**
> I keep hearing that its a BIG commuter campus. and practically dead on the
> weekends ... It's 100% dead on the weekends but you would make friends that
> live on campus and you could see them on weekdays, that doesn't make it any
> harder to see people and make plans.

**4 — ProsConsUNCC.txt**
> So I wanted to get some opinions from students who can definitely mention some
> cons of UNCC instead of campus guides who are paid to only say nice things ...
> Or maybe tell me what parts you love about it!

**5 — ChapelHillCSvsUNCC.txt**
> This is my completely anecdotal experience ... I am a uncc CS 2025 grad and
> work with a chapel hill CS 2025 grad. We discussed salaries and I know I
> started off higher than him and still make more than him ... I was offered an
> extended internship while I was still in college, which resulted in a full
> time offer, and he was not offered any of this.

Each chunk is a complete, self-contained student opinion that could answer a
question on its own.

---

## Embedding Model

Implemented in [`embed.py`](embed.py).

**Model used:** `all-MiniLM-L6-v2` (sentence-transformers), stored in **ChromaDB**
with **cosine** distance and per-chunk metadata (`source` filename + `position`).

**Why:** It runs locally with no API key, no rate limits, and no cost — ideal
for a class project — while still producing strong semantic matches on this
short-text corpus (top-1 retrieval distances of 0.23–0.40 on the test queries).

**Production tradeoff reflection:** If I were deploying for real users and cost
weren't a constraint, I'd weigh: **accuracy on domain text** (a larger model
such as `all-mpnet-base-v2` or an API model like OpenAI `text-embedding-3-large`
captures nuance in slangy student writing better); **context length** (MiniLM
truncates at 256 tokens, which is fine for my 500-char chunks but would lose
information on long-form guides); **multilingual support** (not needed here, but
relevant for a diverse campus); and **latency / hosting** — a local model keeps
data private and avoids per-call cost, while an API model offloads compute but
adds latency, cost, and a dependency. For this project the local model's
zero-cost, low-latency profile clearly wins.

---

## Retrieval Test Results

Top-k = 5, cosine distance (lower = more similar). Results from `python embed.py`:

**Query 1 — "What do students think about Pine Hall?"**
| Rank | Source | Distance |
|---|---|---|
| 1 | PineHall.txt | 0.273 |
| 2 | PineHall.txt | 0.425 |
| 3 | PineHall.txt | 0.440 |
| 4 | ProsConsUNCC.txt | 0.524 |
| 5 | ProsConsUNCC.txt | 0.540 |

*Why these are relevant:* the top three chunks all come from the dedicated Pine
Hall thread and describe the dorm's room size, layout, and location — exactly
the subject of the query. The semantic search surfaced them even though the
query word "think" never appears in the chunks.

**Query 2 — "Is there a party scene at UNC Charlotte?"**
| Rank | Source | Distance |
|---|---|---|
| 1 | PartyUNCC.txt | 0.287 |
| 2 | PartyUNCC.txt | 0.303 |
| 3 | PartyUNCC.txt | 0.449 |
| 4 | ComaprngUNCC.txt | 0.459 |
| 5 | PartyUNCC.txt | 0.478 |

*Why these are relevant:* four of five chunks are from the "Is there a party
scene at UNCC?" thread and directly rate/describe the party scene; the
ComaprngUNCC chunk is a commuter's note on weekend activity, which is on-topic.

**Query 3 — "How is the social life at UNC Charlotte on weekends?"**
| Rank | Source | Distance |
|---|---|---|
| 1 | PartyLifeUNCC.txt | 0.231 |
| 2 | ComaprngUNCC.txt | 0.322 |
| 3 | PartyUNCC.txt | 0.353 |
| 4 | ComaprngUNCC.txt | 0.357 |
| 5 | PartyLifeUNCC.txt | 0.386 |

All top-1 distances are well below the 0.5 checkpoint threshold.

---

## Grounded Generation

Implemented in [`query.py`](query.py), using Groq **`llama-3.3-70b-versatile`**.

**How grounding is enforced** — three mechanisms, not just a polite request:

1. **Strict system prompt.** The model is instructed to answer using *only* the
   provided context, to never use outside knowledge, and — critically — to reply
   with the exact sentence *"I don't have enough information on that."* when the
   context doesn't cover the question.
2. **Out-of-scope distance guard.** Before calling the LLM, if the closest
   retrieved chunk has a cosine distance above `0.75`, the system refuses up
   front without generating — so a question with no relevant documents can't be
   answered from the model's training data.
3. **Programmatic source attribution.** The source list is built from the
   retrieved chunks' metadata in code, not left to the LLM to remember. Citations
   are therefore guaranteed and accurate, and are suppressed when the model
   declines (so a refusal shows no sources).

**How source attribution is surfaced:** `ask()` returns
`{"answer": ..., "sources": [filenames]}`; the Gradio UI renders the answer and a
bulleted "Retrieved from" source list side by side.

---

## Example Responses

**In-scope (sources cited):**

> **Q:** What do students think about Pine Hall?
> **A:** Students say Pine Hall has smaller rooms compared to other dorms like
> Belk or Martin. The building layout is described as a little weird, but its
> location is considered a plus, being close to the Union, parking, and
> education buildings. However, in terms of space, Pine Hall is considered to be
> on the lower end for apartment-style dorms.
> **Sources:** PineHall.txt, ProsConsUNCC.txt

> **Q:** Is there a party scene at UNC Charlotte?
> **A:** Students say there isn't a big party scene at UNC Charlotte. Several
> commenters mention that the party scene is what you make it ... but many
> students commute on weekends ... However, some note that Charlotte has a solid
> nightlife for music events and shows.
> **Sources:** PartyUNCC.txt, ComaprngUNCC.txt

**Out-of-scope (refusal):**

> **Q:** What is the dining hall food like at Stanford?
> **A:** I don't have enough information on that.
> **Sources:** (none)

The system declines rather than fabricating an answer about a school its
documents don't cover.

---

## Query Interface

A **Gradio** web app ([`app.py`](app.py)), launched with `python app.py` at
`http://localhost:7860`.

**Input field:** a single textbox, "Your question."
**Output fields:** "Answer" (the grounded response) and "Retrieved from
(sources)" (a bulleted list of the source documents). Clickable example
questions are provided, including one out-of-scope example.

**Sample interaction transcript:**
```
Your question:  What's Pine Hall like?

Answer:         Students say Pine Hall has smaller rooms compared to other dorms
                like Belk or Martin, and the building layout is a little weird,
                but its location near the Union and parking is a plus.

Retrieved from: • PineHall.txt
                • ProsConsUNCC.txt
```

---

## Evaluation Report

All 5 test questions from [planning.md](planning.md), run through the full system.

| # | Question | Expected answer | System response (summarized) | Retrieval quality | Response accuracy |
|---|----------|-----------------|------------------------------|-------------------|-------------------|
| 1 | What do students think about Pine Hall? | Mostly positive; modern facilities, convenient location | Smaller rooms / "weird" layout, but good location near the Union; lower-end on space | Relevant (top 3 from PineHall.txt) | **Partially accurate** — the documents are more mixed than the "positive" expectation; the system correctly reflected what students actually wrote |
| 2 | What concerns do students have about financial aid? | Delays, communication issues, uncertainty about aid packages | Concern about missing merit-scholarship info and an empty scholarship portal for transfers without a UNCC GPA | Partially relevant (top chunk was a generic post, dedicated aid chunk ranked #2) | **Partially accurate** — narrow; covered the one concern present in the documents but not "delays/communication" |
| 3 | Is there a party scene at UNCC? | Moderate, less active than larger schools | Not a big party scene; commuter campus; findable if you look; Charlotte nightlife is an alternative | Relevant (4/5 from PartyUNCC.txt) | **Accurate** |
| 4 | Major pros and cons of UNCC? | Pros: affordability, opportunities, facilities. Cons: commuter culture, quiet weekends | Pros: value, opportunities/resources, STEM program, self-contained campus. Cons: social scene "in its infancy," empty due to commuting | Relevant (spread across 4 sources) | **Accurate** |
| 5 | Social life on weekends? | Quieter weekends; many students commute/leave | "100% dead on the weekends" (commuter campus), but you can make on-campus friends and see them on weekdays | Relevant (top from PartyLifeUNCC.txt @ 0.231) | **Accurate** |

**Retrieval quality:** Relevant for Q1, Q3, Q4, Q5; Partially relevant for Q2.
**Response accuracy:** Accurate for Q3–Q5; Partially accurate for Q1–Q2.

---

## Failure Case Analysis

**Question that failed:** "What concerns do students have about financial aid at
UNC Charlotte?" (Q2)

**What the system returned:** A narrow answer about a single transfer student not
seeing merit scholarships in the UNCC portal — missing the broader "delays and
communication" themes the expected answer anticipated.

**Root cause (tied to a specific pipeline stage):** This is a
**document-coverage / retrieval** failure, not a generation one. Financial aid
is covered by exactly one source, `FinancialData.txt`, which is the shortest
document in the corpus (only **1 chunk**). With so little material, retrieval
had almost nothing relevant to surface — and in fact the top-ranked chunk
(distance 0.398) was a generic "things you wish you knew" post from
`About_UNCC.txt`, while the genuinely on-topic financial-aid chunk ranked only
#2 (0.431). The LLM then faithfully grounded its answer in thin context, so the
response was accurate to the documents but incomplete relative to the question.

**What I would change to fix it:** Collect more financial-aid documents (more
Reddit threads, the official aid FAQ) so the topic has enough chunks to retrieve
from. Secondarily, add **metadata filtering** (a stretch feature) so an aid
question can prioritize aid-tagged sources, and split long generic posts so a
broad post header doesn't outrank a specific on-topic chunk.

---

## Spec Reflection

**One way the spec helped you during implementation:** Writing the Chunking
Strategy and Architecture sections in [planning.md](planning.md) *before* coding
made implementation unambiguous. The "500 chars / 100 overlap" decision and the
five-stage diagram (Ingestion → Chunking → Embedding/Vector Store → Retrieval →
Generation) mapped almost one-to-one onto the files I built
(`build_chunks.py` → `embed.py` → `query.py` → `app.py`), so I never had to stop
and re-decide architecture mid-build.

**One way your implementation diverged from the spec, and why:** The spec
described a fixed 500-character split. In practice I made 500/100 *targets* and
snapped each boundary to the nearest sentence or word break, because a strict
character cut produced fragments that started or ended mid-word — exactly the
"bad chunk" the assignment warns against. I also added an out-of-scope distance
guard in generation (not in the original plan) after realizing the system
prompt alone was a softer guarantee than a hard pre-LLM check for refusing
questions the documents don't cover.

---

## AI Usage

**Instance 1 — Ingestion & chunking (`build_chunks.py`)**

- *What I gave the AI:* My planning.md Documents section (10 Reddit `.txt`
  files), Chunking Strategy (500/100), and the architecture diagram.
- *What it produced:* A load → clean → chunk script writing `chunks.json`.
- *What I changed or overrode:* I inspected real chunks and iteratively directed
  the cleaning to strip artifacts the first version missed — usernames,
  abbreviated timestamps (`4y ago`), vote-count numbers, `Promoted` ad blocks
  (including the free-text ad copy), and "Archived post" notices. I also changed
  the chunker from a hard 500-char cut to **word-boundary snapping** so chunks
  stopped beginning mid-word.

**Instance 2 — Embedding, retrieval & grounded generation (`embed.py`, `query.py`)**

- *What I gave the AI:* My Retrieval Approach section (all-MiniLM-L6-v2,
  top-k=5, ChromaDB) and my grounding requirement (answer from context only,
  cite sources, refuse when uncovered).
- *What it produced:* An embedding/retrieval module and a Groq-backed generation
  function.
- *What I changed or overrode:* I configured ChromaDB to use **cosine** distance
  so scores matched the checkpoint's <0.5 expectation, added a **distance-based
  out-of-scope guard** for refusals, and made **source attribution programmatic**
  (built from chunk metadata) instead of trusting the LLM to cite reliably.

---

## Known Limitations

- A few comment chunks retain a stray bare username (e.g. a one-word reply
  immediately following a handle) that the username heuristic doesn't catch,
  since it keys on a following timestamp/separator. This is cosmetic and does
  not affect retrieval relevance.
- Financial-aid coverage is thin (one short source) — see Failure Case Analysis.
