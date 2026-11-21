
from modules.rag_engine import retrieve_context
from modules.vector_rag import vector_search
from knowledge_graph.graph_engine import find_related_threats


def hybrid_retrieve(question, top_k=8):
    """
    Combine keyword, vector and graph retrieval.
    Rank and remove duplicate threat records.
    """

    combined = {}

    def add_result(item, method, content_key="content"):
        title = item.get("title", "Unknown")
        key = title.strip().lower()

        if key not in combined:
            combined[key] = {
                "title": title,
                "content": item.get(
                    content_key,
                    item.get("description", "")
                ),
                "category": item.get("category", "Unknown"),
                "source": item.get("source", "Knowledge Graph"),
                "retrieval_method": method,
                "score": 0,
                "evidence_methods": []
            }

        record = combined[key]

        if method not in record["evidence_methods"]:
            record["evidence_methods"].append(method)
            record["score"] += {
                "Keyword RAG": 3,
                "Vector RAG": 3,
                "GraphRAG": 2
            }.get(method, 1)

    # 1. Keyword retrieval
    try:
        keyword_results = retrieve_context(
            question,
            top_k=top_k
        )

        for item in keyword_results:
            add_result(item, "Keyword RAG")

    except Exception as error:
        print("Keyword retrieval error:", error)

    # 2. Semantic vector retrieval
    try:
        vector_results = vector_search(
            question,
            top_k=top_k
        )

        for item in vector_results:
            add_result(item, "Vector RAG")

    except Exception as error:
        print("Vector retrieval error:", error)

    # 3. Knowledge graph retrieval
    try:
        graph_results = find_related_threats(
            question,
            top_k=top_k
        )

        for item in graph_results:
            add_result(
                item,
                "GraphRAG",
                content_key="description"
            )

    except Exception as error:
        print("Graph retrieval error:", error)

    # 4. Combine retrieval methods
    results = list(combined.values())

    for item in results:
        item["retrieval_method"] = " + ".join(
            item.pop("evidence_methods")
        )

    # 5. Rank by combined retrieval score
    results.sort(
        key=lambda item: item["score"],
        reverse=True
    )

    return results[:top_k]


def build_hybrid_context(question):
    """Build evidence context from hybrid retrieval."""

    results = hybrid_retrieve(question)

    if not results:
        return "No relevant evidence found.", []

    context_parts = []

    for item in results:
        context_parts.append(
            f"Title: {item['title']}\n"
            f"Category: {item['category']}\n"
            f"Information: {item['content']}\n"
            f"Source: {item['source']}\n"
            f"Retrieval: {item['retrieval_method']}\n"
            f"Combined Score: {item['score']}"
        )

    return "\n\n".join(context_parts), results
