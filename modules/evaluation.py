
from modules.rag_engine import retrieve_context
from modules.vector_rag import vector_search
from modules.graphrag_engine import hybrid_retrieve


# Small, manually labelled evaluation dataset.
# Expected documents are based on the current CyberIntel dataset.
TEST_CASES = [
    {
        "question": "Explain Log4Shell vulnerability",
        "relevant": [
            "Log4Shell Vulnerability",
            "Apache Log4j",
            "Remote Code Execution",
            "MITRE ATT&CK T1190"
        ]
    },
    {
        "question": "Which software is affected by Log4Shell?",
        "relevant": [
            "Log4Shell Vulnerability",
            "Apache Log4j"
        ]
    },
    {
        "question": "How can Log4Shell lead to remote code execution?",
        "relevant": [
            "Log4Shell Vulnerability",
            "Remote Code Execution"
        ]
    }
]


def normalize_results(results):
    """Convert retrieval outputs into a consistent list of titles."""

    if results is None:
        return []

    if isinstance(results, dict):
        results = [results]

    if isinstance(results, str):
        return []

    titles = []

    for item in results:
        if isinstance(item, dict):
            title = item.get("title") or item.get("name")
            if title:
                titles.append(title.strip().lower())

    return titles


def precision_at_k(retrieved, relevant, k):
    retrieved_k = retrieved[:k]

    if not retrieved_k:
        return 0.0

    relevant_count = sum(
        1 for title in retrieved_k if title in relevant
    )

    return relevant_count / k


def recall_at_k(retrieved, relevant, k):
    if not relevant:
        return 0.0

    retrieved_k = retrieved[:k]

    relevant_count = sum(
        1 for title in retrieved_k if title in relevant
    )

    return relevant_count / len(relevant)


def mean_reciprocal_rank(retrieved, relevant):
    for rank, title in enumerate(retrieved, start=1):
        if title in relevant:
            return 1 / rank

    return 0.0


def evaluate_method(method_name, retrieval_function, top_k=5):
    scores = []

    print("\n" + "=" * 60)
    print(method_name)
    print("=" * 60)

    for test in TEST_CASES:
        question = test["question"]
        relevant = {
            title.lower() for title in test["relevant"]
        }

        try:
            results = retrieval_function(question, top_k)
            retrieved = normalize_results(results)

            precision = precision_at_k(
                retrieved, relevant, top_k
            )

            recall = recall_at_k(
                retrieved, relevant, top_k
            )

            mrr = mean_reciprocal_rank(
                retrieved, relevant
            )

            scores.append({
                "precision": precision,
                "recall": recall,
                "mrr": mrr
            })

            print("\nQuestion:", question)
            print("Retrieved:", retrieved)
            print(f"Precision@{top_k}: {precision:.3f}")
            print(f"Recall@{top_k}: {recall:.3f}")
            print(f"MRR: {mrr:.3f}")

        except Exception as error:
            print("\nQuestion:", question)
            print("Evaluation error:", error)

    if not scores:
        print("\nNo successful evaluations.")
        return None

    average = {
        metric: sum(item[metric] for item in scores) / len(scores)
        for metric in ("precision", "recall", "mrr")
    }

    print("\nAVERAGE RESULTS")
    print(f"Precision@{top_k}: {average['precision']:.3f}")
    print(f"Recall@{top_k}: {average['recall']:.3f}")
    print(f"MRR: {average['mrr']:.3f}")

    return average


def keyword_adapter(question, top_k):
    return retrieve_context(question)


def vector_adapter(question, top_k):
    return vector_search(question, top_k=top_k)


def hybrid_adapter(question, top_k):
    return hybrid_retrieve(question, top_k=top_k)


def run_evaluation():
    results = {}

    methods = [
        ("Keyword RAG", keyword_adapter),
        ("Vector RAG", vector_adapter),
        ("Hybrid GraphRAG", hybrid_adapter)
    ]

    for name, function in methods:
        results[name] = evaluate_method(name, function)

    print("\n" + "=" * 60)
    print("FINAL COMPARISON")
    print("=" * 60)

    for name, metrics in results.items():
        if metrics:
            print(
                f"{name}: "
                f"Precision={metrics['precision']:.3f}, "
                f"Recall={metrics['recall']:.3f}, "
                f"MRR={metrics['mrr']:.3f}"
            )


if __name__ == "__main__":
    run_evaluation()
