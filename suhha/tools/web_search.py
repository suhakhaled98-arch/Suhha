"""Lightweight web search + fetch, no API key required.

Uses DuckDuckGo's HTML endpoint for search results and a simple GET+strip
for fetching a page's text. Good enough for "look this up and summarize it"
tasks; swap in a paid search API here if you need higher quality results.
"""
import re
from html import unescape

import requests

USER_AGENT = "SuhhaAgent/1.0 (personal automation tool)"


def search(query: str, max_results: int = 5) -> list[dict]:
    resp = requests.post(
        "https://html.duckduckgo.com/html/",
        data={"q": query},
        headers={"User-Agent": USER_AGENT},
        timeout=15,
    )
    resp.raise_for_status()

    results = []
    for match in re.finditer(
        r'<a rel="nofollow" class="result__a" href="([^"]+)">(.*?)</a>.*?'
        r'class="result__snippet"[^>]*>(.*?)</a>',
        resp.text,
        re.DOTALL,
    ):
        url, title, snippet = match.groups()
        results.append(
            {
                "url": unescape(url),
                "title": unescape(re.sub("<.*?>", "", title)).strip(),
                "snippet": unescape(re.sub("<.*?>", "", snippet)).strip(),
            }
        )
        if len(results) >= max_results:
            break
    return results


def fetch_text(url: str, max_chars: int = 6000) -> str:
    resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=15)
    resp.raise_for_status()
    text = re.sub(r"<script.*?</script>|<style.*?</style>", "", resp.text, flags=re.DOTALL)
    text = re.sub(r"<[^>]+>", " ", text)
    text = unescape(re.sub(r"\s+", " ", text)).strip()
    return text[:max_chars]
