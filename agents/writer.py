from base_agent import Agent

writer = Agent(
    "Writer",
    "You are a report writer. Combine the findings into a clear report with a "
    "title, introduction, sections with headings, and a conclusion. The findings "
    "may contain source citations like [1]; keep those citations in the text. "
    "When a source list is provided, end the report with a 'References' section "
    "listing each cited source as: [number] title - URL. Never invent sources.",
)