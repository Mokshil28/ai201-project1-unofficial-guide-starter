"""
Milestone 5 — Gradio query interface for The Unofficial Guide.

Run:
    python app.py
Then open http://localhost:7860

Type a question about UNC Charlotte; the system retrieves relevant student
posts, generates a grounded answer, and lists the source documents it drew from.
"""

import gradio as gr

from query import ask

EXAMPLES = [
    "What do students think about Pine Hall?",
    "Is there a party scene at UNC Charlotte?",
    "What are the major pros and cons of UNC Charlotte?",
    "How is the social life at UNC Charlotte on weekends?",
    "What is the dining hall food like at Stanford?",  # out-of-scope -> should refuse
]


def handle_query(question):
    if not question or not question.strip():
        return "Please enter a question.", ""
    result = ask(question)
    sources = "\n".join(f"• {s}" for s in result["sources"]) or "(no sources — not covered by the documents)"
    return result["answer"], sources


with gr.Blocks(title="The Unofficial Guide — UNC Charlotte") as demo:
    gr.Markdown(
        "# The Unofficial Guide — UNC Charlotte\n"
        "Ask about housing, social life, financial aid, academics, and more — "
        "answered from real student posts, with sources cited."
    )
    inp = gr.Textbox(label="Your question", placeholder="e.g. What's Pine Hall like?")
    btn = gr.Button("Ask", variant="primary")
    answer = gr.Textbox(label="Answer", lines=8)
    sources = gr.Textbox(label="Retrieved from (sources)", lines=4)

    btn.click(handle_query, inputs=inp, outputs=[answer, sources])
    inp.submit(handle_query, inputs=inp, outputs=[answer, sources])
    gr.Examples(examples=EXAMPLES, inputs=inp)


if __name__ == "__main__":
    demo.launch()
