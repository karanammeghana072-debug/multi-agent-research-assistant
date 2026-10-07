import os
from dotenv import load_dotenv

load_dotenv()


def search_web(query, max_results=3):
    """Search the web with Tavily. Returns a list of {title, url, content}.
    Returns an empty list if no key is set or the search fails, so the app still works."""
    key = os.getenv("TAVILY_API_KEY")
    if not key:
        return []
    try:
        from tavily import TavilyClient

        res = TavilyClient(api_key=key).search(
            query=query, max_results=max_results, search_depth="basic"
        )
        return [
            {
                "title": (r.get("title") or "").strip(),
                "url": r.get("url", ""),
                "content": (r.get("content") or "")[:700],
            }
            for r in res.get("results", [])
        ]
    except Exception as e:
        print("[Retriever] search failed:", e)
        return []