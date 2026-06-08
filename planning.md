# Project 1 Planning: The Unofficial Guide

> Write this document before you write any pipeline code.
> Your spec and architecture diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Update the Retrieval Approach and Chunking Strategy sections if you change your approach during implementation.
> Update this file before starting any stretch features.

---

## Domain

<!-- What domain did you choose? Why is this knowledge valuable and hard to find through official channels? -->

My domain is student experiences at UNC Charlotte. This includes housing, social life, financial aid, campus culture, and computer science student experiences.

This knowledge is valuable because official university websites provide policies and marketing information, but students often need honest opinions and real-world experiences that are only shared on Reddit and student communities.
---

## Documents

<!-- List your specific sources: URLs, subreddit names, forum threads, or file descriptions.
     Aim for at least 10 sources that together cover different subtopics or perspectives within your domain. -->

| # | Source | Description | URL or location |
|---|--------|-------------|-----------------|
| 1 | Reddit| What's something you wish you knew about UNCC before attending?  | https://www.reddit.com/r/UNCCharlotte/comments/1o6uimn/whats_something_you_wish_you_knew_about_uncc/ |
| 2 | Reddit|What's Pine Hall Like? |https://www.reddit.com/r/UNCCharlotte/comments/1tzn2uc/whats_pine_hall_like/ |
| 3 | Reddit|Financial Aid |https://www.reddit.com/r/UNCCharlotte/comments/1tztly1/financial_aid/ |
| 4 | Reddit |oak hall |https://www.reddit.com/r/UNCCharlotte/comments/1tzth7n/oak_hall/ |
| 5 | Reddit|Student Life at UNCC? | https://www.reddit.com/r/UNCCharlotte/comments/1s8ltik/student_life_at_uncc/ |
| 6 | Reddit |Pros and Cons of UNCC? |https://www.reddit.com/r/UNCCharlotte/comments/u051kn/pros_and_cons_of_uncc/ |
| 7 | Reddit |How is uncc? |https://www.reddit.com/r/UNCCharlotte/comments/1qhlbyr/how_is_uncc/ |
| 8 | Reddit | Chapel Hill or UNCC For Computer Science? Please Help |https://www.reddit.com/r/UNCCharlotte/comments/1retd57/chapel_hill_or_uncc_for_computer_science_please/ |
| 9 | Reddit | Is there a party scene at UNCC? |https://www.reddit.com/r/UNCCharlotte/comments/1pr3mg2/is_there_a_party_scene_at_uncc/ |
| 10 | Reddit | How is the social life at UNCC? Is it really dead on the weekends?| https://www.reddit.com/r/UNCCharlotte/comments/1ojlp8i/how_is_the_social_life_at_uncc_is_it_really_dead/|

---

## Chunking Strategy

<!-- How will you split documents into chunks?
     State your chunk size (in tokens or characters), overlap size, and explain why those
     numbers fit the structure of your documents.
     A review-heavy corpus warrants different chunking than a long FAQ. -->

**Chunk size:**: 500 Characters 

**Overlap:** 100 Characters

**Reasoning:** My documents consist primarily of Reddit posts and comments, which are usually short and opinion-based. A chunk size of 500 characters is large enough to preserve complete student experiences while still allowing retrieval of specific topics. A 100-character overlap helps ensure that important information split between chunks is not lost during retrieval.

---

## Retrieval Approach

<!-- Which embedding model are you using (e.g., all-MiniLM-L6-v2 via sentence-transformers)?
     How many chunks will you retrieve per query (top-k)?
     If you were deploying this for real users and cost wasn't a constraint, what tradeoffs
     would you weigh in choosing a different embedding model — context length, multilingual
     support, accuracy on domain-specific text, latency? -->

**Embedding model:** all-MiniLM-L6-v2 (sentence-transformers)

**Top-k:** 5

**Production tradeoff reflection:** The all-MiniLM-L6-v2 model is lightweight, free, and fast for local development. For a production system, I would consider larger embedding models that provide better semantic understanding, support multiple languages, and improve retrieval accuracy. However, larger models increase latency and infrastructure costs.

---

## Evaluation Plan

<!-- List your 5 test questions with their expected correct answers.
     Questions should be specific enough that you can judge whether the system's response
     is right or wrong. "What are good dining halls?" is too vague.
     "What do students say about wait times at [dining hall name] during lunch?" is testable. -->

| # | Question | Expected answer |
|---|----------|-----------------|
| 1 | What do students think about Pine Hall? | Most students describe Pine Hall positively, mentioning modern facilities and convenient location. |
| 2 | What concerns do students have about financial aid at UNC Charlotte? | Students report delays, communication issues, and uncertainty regarding aid packages. |
| 3 | Is there a party scene at UNC Charlotte? | Students generally describe the party scene as moderate and less active than larger universities. |
| 4 | What are the major pros and cons of UNC Charlotte? | Pros include affordability, growing opportunities, and campus facilities. Cons include commuter culture and quieter weekends. |
| 5 | How is the social life at UNC Charlotte on weekends? | Many students report quieter weekends because a significant number of students commute or leave campus. |

---

## Anticipated Challenges

<!-- What could go wrong? Name at least two specific risks with reasoning.
     Consider: noisy or inconsistent documents, missing source attribution, off-topic
     retrieval, chunks that split key information across boundaries. -->
 1. Reddit posts contain subjective opinions that may conflict with each other, making it difficult to produce a single definitive answer.

2. Retrieval may return comments that are only partially relevant to the user's question because different discussions often overlap topics such as housing, social life, and academics.

3. Important information may be split across chunk boundaries, causing retrieval to miss part of the context needed for a complete answer.

4. Source attribution may become difficult if metadata is not stored correctly with each chunk.
---

## Architecture

<!-- Draw a diagram of your pipeline showing the five stages:
     Document Ingestion → Chunking → Embedding + Vector Store → Retrieval → Generation
     Label each stage with the tool or library you're using.
     You can use ASCII art, a Mermaid diagram, or embed a sketch as an image.
     You'll use this diagram as context when prompting AI tools to implement each stage. -->

Documents (Reddit Threads)
        |
        v
Document Ingestion
(Python)
        |
        v
Text Cleaning
        |
        v
Chunking
(500 chars, 100 overlap)
        |
        v
Embeddings
(all-MiniLM-L6-v2)
        |
        v
ChromaDB
(Vector Store)
        |
        v
Retrieval
(Top 5 Chunks)
        |
        v
Groq Llama 3.3
        |
        v
Answer + Source Citations
---

## AI Tool Plan

<!-- For each part of the pipeline below, describe:
     - Which AI tool you plan to use (Claude, Copilot, ChatGPT, etc.)
     - What you'll give it as input (which sections of this planning.md, which requirements)
     - What you expect it to produce
     - How you'll verify the output matches your spec

     "I'll use AI to help me code" is not a plan.
     "I'll give Claude my Chunking Strategy section and ask it to implement chunk_text()
     with my specified chunk size and overlap" is a plan. -->

**Milestone 3 — Ingestion and chunking:**
I will use Claude Code to help implement document ingestion, text cleaning, and chunking. I will provide Claude Code with my Documents section, Chunking Strategy, and Architecture diagram from this planning document. I expect it to generate Python scripts that load my Reddit thread data, clean unnecessary text, and split the documents into chunks using my specified chunk size and overlap. I will verify the implementation by inspecting sample chunks and ensuring they are readable, self-contained, and match my chunking strategy.

**Milestone 4 — Embedding and retrieval:**
I will use Claude Code to implement embeddings with the all-MiniLM-L6-v2 model and store vectors in ChromaDB. I will provide Claude Code with my Retrieval Approach section and Architecture diagram. I expect it to generate code for embedding documents, storing metadata, and retrieving the top-k most relevant chunks for a query. I will verify the implementation by testing retrieval on my evaluation questions and checking whether the returned chunks are relevant and correctly sourced.

**Milestone 5 — Generation and interface:**
I will use Claude Code to connect retrieval to Groq's llama-3.3-70b-versatile model and build a Gradio interface. I will provide Claude Code with my grounding requirements, retrieval design, and desired output format. I expect it to generate code that answers questions using only retrieved context and includes source attribution in every response. I will verify the implementation by testing both supported and unsupported questions and ensuring the system refuses to answer when sufficient information is not available in the documents.
