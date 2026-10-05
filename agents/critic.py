from base_agent import Agent

critic = Agent(
    "Critic",
    "You are a strict report reviewer. Review the report and give 3-5 "
    "short bullet points on what to fix: missing facts, unclear parts, "
    "weak structure. Do not rewrite the report.",
)
