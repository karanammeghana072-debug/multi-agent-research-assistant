import json
from flask import Flask, Response, render_template, request

from agents.planner import planner
from agents.researcher import researcher
from agents.writer import writer
from agents.critic import critic
from base_agent import get_model

app = Flask(__name__)


def send(**data):
    return json.dumps(data) + "\n"


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
            yield send(type="model", name=get_model())

            yield send(type="stage", stage="planner")
            questions = [q.strip() for q in planner.run(topic).split("\n") if q.strip()]
            yield send(type="questions", items=questions)

            yield send(type="stage", stage="researcher")
            findings = []
            for i, q in enumerate(questions):
                answer = researcher.run(q)
                findings.append(f"Q: {q}\nA: {answer}")
                yield send(type="answer", index=i, text=answer)
            findings_text = "\n\n".join(findings)

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