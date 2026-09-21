"""GitHub project tracking via the REST API using a personal access token."""
import requests

from ..config import GITHUB_DEFAULT_REPO, GITHUB_TOKEN

API_ROOT = "https://api.github.com"


def _headers() -> dict:
    if not GITHUB_TOKEN:
        raise RuntimeError("GITHUB_TOKEN مش متظبط في .env")
    return {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
    }


def _repo(repo: str | None) -> str:
    repo = repo or GITHUB_DEFAULT_REPO
    if not repo:
        raise RuntimeError("محدّدتيش repo، حطي GITHUB_DEFAULT_REPO أو ابعتيه في الطلب")
    return repo


def list_open_issues(repo: str | None = None, limit: int = 10) -> list[dict]:
    resp = requests.get(
        f"{API_ROOT}/repos/{_repo(repo)}/issues",
        headers=_headers(),
        params={"state": "open", "per_page": limit},
        timeout=15,
    )
    resp.raise_for_status()
    return [
        {"number": i["number"], "title": i["title"], "url": i["html_url"]}
        for i in resp.json()
        if "pull_request" not in i
    ]


def list_open_pull_requests(repo: str | None = None, limit: int = 10) -> list[dict]:
    resp = requests.get(
        f"{API_ROOT}/repos/{_repo(repo)}/pulls",
        headers=_headers(),
        params={"state": "open", "per_page": limit},
        timeout=15,
    )
    resp.raise_for_status()
    return [
        {"number": p["number"], "title": p["title"], "url": p["html_url"]}
        for p in resp.json()
    ]


def create_issue(title: str, body: str = "", repo: str | None = None) -> dict:
    resp = requests.post(
        f"{API_ROOT}/repos/{_repo(repo)}/issues",
        headers=_headers(),
        json={"title": title, "body": body},
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    return {"number": data["number"], "url": data["html_url"]}


def comment_on_issue(number: int, body: str, repo: str | None = None) -> dict:
    resp = requests.post(
        f"{API_ROOT}/repos/{_repo(repo)}/issues/{number}/comments",
        headers=_headers(),
        json={"body": body},
        timeout=15,
    )
    resp.raise_for_status()
    return {"url": resp.json()["html_url"]}
