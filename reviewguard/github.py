"""Read public GitHub PR diffs through GitHub's API."""
import re
import requests

PR_PATTERN = re.compile(r"^https://github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)/pull/(\d+)(?:/)?(?:\?.*)?$", re.I)

def fetch_public_pr_diff(url, token=None):
    match = PR_PATTERN.fullmatch(url.strip())
    if not match:
        raise ValueError("Expected a public https://github.com/OWNER/REPO/pull/NUMBER URL")
    owner, repo, number = match.groups()
    headers = {"Accept": "application/vnd.github.v3.diff", "User-Agent": "ReviewGuard-Assessment/1.0"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    response = requests.get(
        f"https://api.github.com/repos/{owner}/{repo}/pulls/{number}",
        headers=headers,
        timeout=15,
        allow_redirects=False,
    )
    response.raise_for_status()
    if len(response.content) > 250_000:
        raise ValueError("PR diff exceeds 250 KB limit")
    if not response.text.startswith("diff --git "):
        raise ValueError("GitHub did not return a unified diff; check permissions and rate limits")
    return response.text