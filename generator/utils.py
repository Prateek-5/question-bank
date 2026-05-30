"""Helpers for DSA repo generation."""
import re
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'DSA'))

EMOJI_RE = re.compile(
    "["
    "\U0001F300-\U0001FAFF"
    "\U00002600-\U000027BF"
    "\U0001F1E0-\U0001F1FF"
    "\uFE00-\uFE0F"
    "]+",
    flags=re.UNICODE,
)

def clean_topic(name: str) -> str:
    n = EMOJI_RE.sub("", name)
    n = n.replace("&", "and").replace("/", " ").replace("(", " ").replace(")", " ")
    n = re.sub(r"[^A-Za-z0-9 ]", " ", n)
    n = re.sub(r"\s+", " ", n).strip()
    return n.replace(" ", "_")

def clean_title(name: str) -> str:
    n = EMOJI_RE.sub("", name)
    n = n.replace("&", "and")
    n = re.sub(r"[^A-Za-z0-9 ]", " ", n)
    n = re.sub(r"\s+", " ", n).strip()
    return n.replace(" ", "_")

def write(path: str, content: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def make_question_md(title, link, topic, q):
    """q: dict with concept, intuition, explanation, dry_run, approach, complexity, code, followups."""
    link_html = (
        f'<a href="{link}" target="_blank" rel="noopener noreferrer">{link}</a>'
        if link else ""
    )
    return f"""# {title}

## Problem Link
{link_html}

## Topic
{topic}

## Core Concept
{q['concept']}

## Intuition
{q['intuition']}

## Detailed Explanation
{q['explanation']}

## Dry Run
{q['dry_run']}

## Approach
{q['approach']}

## Time and Space Complexity
{q['complexity']}

## C++ Implementation
```cpp
{q['code']}
```

## Follow-up Questions
{q['followups']}
"""
