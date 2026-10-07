import json
import os
from flask import Flask, Response, render_template, request

from agents.planner import planner
from agents.researcher import researcher
from agents.writer import writer
from agents.critic import critic
from base_agent import get_model
from retriever import search_web

app = Flask(__name__)


def send(**data):
    return json.dumps(data) + "\n"


def safe(text):
    return text.replace("[", "(").replace("]", ")")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/research", methods=["POST"])
def research():
    topic = (request.get_json(silent=True) or {}).get("topic", "").strip()
    if not topic:
        return Response(send(type="error", message="Enter a topic first."), mimetype="application/x-ndjson")

    def run():
        try:
            label = get_model() + (" + web search" if os.getenv("TAVILY_API_KEY") else "")
            yield send(type="model", name=label)

            yield send(type="stage", stage="planner")
            questions = [q.strip() for q in planner.run(topic).split("\n") if q.strip()]
            yield send(type="questions", items=questions)

            yield send(type="stage", stage="researcher")
            findings, all_sources = [], []
            for i, q in enumerate(questions):
                # RETRIEVE: search the web for this question
                found = search_web(q)
                for s in found:
                    s["n"] = len(all_sources) + 1
                    all_sources.append(s)

                # AUGMENT: put the retrieved text into the prompt
                if found:
                    context = "\n\n".join(
                        f"[{s['n']}] {s['title']} ({s['url']})\n{s['content']}" for s in found
                    )
                    task = f"Question: {q}\n\nSources:\n{context}"
                else:
                    task = f"Question: {q}\n\n(No web sources are available. Answer from general knowledge.)"

                # GENERATE: the model answers using the sources
                answer = researcher.run(task)
                findings.append(f"Q: {q}\nA: {answer}")

                shown = answer
                if found:
                    shown += "\n\n**Sources:** " + " | ".join(
                        f"[{s['n']}] [{safe(s['title']) or s['url']}]({s['url']})" for s in found
                    )
                yield send(type="answer", index=i, text=shown)

            findings_text = "\n\n".join(findings)
            if all_sources:
                findings_text += "\n\nSource list:\n" + "\n".join(
                    f"[{s['n']}] {s['title']} - {s['url']}" for s in all_sources
                )

            yield send(type="stage", stage="writer")
            draft = writer.run(f"Topic: {topic}\n\nFindings:\n\n{findings_text}")
            yield send(type="draft", text=draft)

            yield send(type="stage", stage="critic")
            feedback = critic.run(draft)
            yield send(type="feedback", text=feedback)

            yield send(type="stage", stage="rewrite")
            final = writer.run(
                f"Topic: {topic}\n\nFindings:\n\n{findings_text}\n\n"
                f"Your draft:\n{draft}\n\nCritic feedback:\n{feedback}\n\n"
                "Rewrite the report and fix every point in the feedback."
            )
            yield send(type="report", text=final)
            yield send(type="done")
        except Exception as e:
            yield send(type="error", message=str(e))

    return Response(run(), mimetype="application/x-ndjson")


if __name__ == "__main__":
    app.run(debug=True, port=5000)