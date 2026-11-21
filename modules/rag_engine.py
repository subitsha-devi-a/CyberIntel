
import json
import re
from pathlib import Path
from collections import Counter

DATA_FILE = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "threats.json"
)

STOP_WORDS = {
    "the", "is", "are", "was", "were", "and", "or",
    "to", "of", "in", "on", "for", "a", "an", "with",
    "what", "how", "explain", "about", "possible",
    "its", "their", "this", "that", "relationship",
    "discovery", "context", "please"
}


def load_threats():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def tokenize(text):
    words = re.findall(r"[a-zA-Z0-9-]+", text.lower())
    return [
        word for word in words
        if word not in STOP_WORDS and len(word) > 1
    ]


def retrieve_context(question, top_k=5):

    threats = load_threats()
    question_words = set(tokenize(question))

    if not question_words:
        return []

    scored_results = []

    for threat in threats:

        title_words = set(tokenize(threat.get("title", "")))
        content_words = set(tokenize(threat.get("content", "")))
        category_words = set(tokenize(threat.get("category", "")))

        score = (
            len(question_words & title_words) * 5
            + len(question_words & category_words) * 3
            + len(question_words & content_words)
        )

        if score > 0:
            scored_results.append((score, threat))

    scored_results.sort(
        key=lambda item: item[0],
        reverse=True
    )

    return [
        {
            "title": threat["title"],
            "content": threat["content"],
            "source": threat["source"],
            "category": threat["category"],
            "score": score
        }
        for score, threat in scored_results[:top_k]
    ]


def build_context(question):

    results = retrieve_context(question)

    if not results:
        return "No relevant cybersecurity records were found.", []

    context = "\n\n".join(
        f"Title: {item['title']}\n"
        f"Category: {item['category']}\n"
        f"Information: {item['content']}\n"
        f"Source: {item['source']}"
        for item in results
    )

    return context, results
