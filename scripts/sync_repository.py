"""Update snapshot URLs and project metadata after a GitHub repository rename.

Only touches project.json and the two exact GitHub snapshot sources in the
standalone loader. The next build.py then embeds the new URLs into index.html.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sync() -> bool:
    location = os.environ.get("GITHUB_REPOSITORY")
    if not location:
        print("GITHUB_REPOSITORY unset; leaving snapshot URLs unchanged")
        return False
    if not re.fullmatch(r"[A-Za-z0-9-]+/[A-Za-z0-9_.-]+", location):
        raise ValueError("Unexpected GitHub repository identifier")
    owner, repo = location.split("/", 1)
    config_file = ROOT / "project.json"
    config = json.loads(config_file.read_text(encoding="utf-8"))
    old = config.get("github", {})
    config["github"] = {"owner": owner, "repo": repo}
    source = (ROOT / "web/snapshot-loader.js").read_text(encoding="utf-8")
    expected = (
        r"https://raw\.githubusercontent\.com/[A-Za-z0-9-]+/[A-Za-z0-9_.-]+/main/data/snapshot\.json",
        r"https://api\.github\.com/repos/[A-Za-z0-9-]+/[A-Za-z0-9_.-]+/contents/data/snapshot\.json\?ref=main",
    )
    changes = (
        "https://raw.githubusercontent.com/" + location + "/main/data/snapshot.json",
        "https://api.github.com/repos/" + location + "/contents/data/snapshot.json?ref=main",
    )
    new = source
    for pattern, url in zip(expected, changes):
        new, count = re.subn(pattern, lambda _: url, new, count=1)
        if count != 1:
            raise ValueError("Missing canonical snapshot source URL in loader")
    page_file = ROOT / "web/page.html"
    page = page_file.read_text(encoding="utf-8")
    page_new, links = re.subn(
        r'href="https://github\.com/[A-Za-z0-9-]+/[A-Za-z0-9_.-]+">GitHub</a>',
        lambda _: 'href="https://github.com/' + location + '">GitHub</a>',
        page, count=1)
    if links != 1:
        raise ValueError("Missing MEM GitHub button in page template")
    changed = config.get("github") != old or new != source or page_new != page
    if changed:
        config_file.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (ROOT / "web/snapshot-loader.js").write_text(new, encoding="utf-8")
        page_file.write_text(page_new, encoding="utf-8")
        print("Synchronized MEM Observatory GitHub URL and snapshot sources to", location)
    return changed


if __name__ == "__main__":
    sync()
