#!/usr/bin/env python3
"""Intent parser — extracts keywords from intent for RAG retrieval."""

import re


def parse(raw_intent: str) -> dict:
    """
    Extract structured info from raw intent string.
    Used by retriever to find relevant past sessions.
    Returns dict with keywords for FTS search.
    """
    # strip punctuation, lowercase, split
    cleaned = re.sub(r"[^\w\s]", " ", raw_intent.lower())
    words = cleaned.split()

    # filter stopwords
    stopwords = {"a", "an", "the", "and", "or", "to", "in", "on", "at",
                 "for", "with", "my", "me", "i", "it", "is", "do", "can",
                 "please", "just", "get", "make", "run", "use", "want"}
    keywords = [w for w in words if w not in stopwords and len(w) > 2]

    return {
        "raw": raw_intent,
        "keywords": keywords,
        "fts_query": " OR ".join(keywords[:5]),  # top 5 keywords for FTS
    }


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("intent", type=str)
    args = parser.parse_args()
    import json
    print(json.dumps(parse(args.intent), indent=2))
