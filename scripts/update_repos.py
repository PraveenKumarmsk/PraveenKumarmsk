"""Rebuilds the repository table inside README.md from the GitHub API.

Runs inside GitHub Actions (see .github/workflows/update-repos.yml).
Everything between <!-- REPOS:START --> and <!-- REPOS:END --> is replaced.
"""
import json
import os
import re
import urllib.request

OWNER = os.environ.get("GITHUB_REPOSITORY_OWNER", "PraveenKumarmsk")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
README = "README.md"
START, END = "<!-- REPOS:START -->", "<!-- REPOS:END -->"


def fetch_repos():
    repos, page = [], 1
    while True:
        url = (
            f"https://api.github.com/users/{OWNER}/repos"
            f"?per_page=100&page={page}&type=owner&sort=pushed"
        )
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "profile-readme-updater",
        }
        if TOKEN:
            headers["Authorization"] = f"Bearer {TOKEN}"
        with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=30) as r:
            data = json.load(r)
        repos.extend(data)
        if len(data) < 100:
            break
        page += 1
    return repos


def cell(text):
    return (text or "").replace("|", "\\|").replace("\n", " ").strip()


def build_table(repos):
    # skip the profile repo itself (same name as the username)
    repos = [r for r in repos if r["name"].lower() != OWNER.lower()]
    repos.sort(key=lambda r: r.get("pushed_at") or "", reverse=True)
    rows = ["| Repository | Description | Language | ★ |", "|:--|:--|:--|:--:|"]
    for r in repos:
        name = f"[**{cell(r['name'])}**]({r['html_url']})"
        if r.get("fork"):
            name += " _(fork)_"
        desc = cell(r.get("description")) or "—"
        lang = cell(r.get("language")) or "—"
        stars = r.get("stargazers_count", 0)
        rows.append(f"| {name} | {desc} | {lang} | {stars} |")
    rows.append("")
    rows.append(f"_Auto-updated · {len(repos)} public repositories_")
    return "\n".join(rows)


def main():
    repos = fetch_repos()
    if not repos:
        print("No repos returned, leaving README unchanged.")
        return
    with open(README, encoding="utf-8") as f:
        text = f.read()
    pattern = re.compile(re.escape(START) + r".*?" + re.escape(END), re.S)
    if not pattern.search(text):
        raise SystemExit("Markers not found in README.md")
    block = f"{START}\n\n{build_table(repos)}\n\n{END}"
    new = pattern.sub(lambda _: block, text)
    if new != text:
        with open(README, "w", encoding="utf-8") as f:
            f.write(new)
        print("README updated.")
    else:
        print("No changes.")


if __name__ == "__main__":
    main()
