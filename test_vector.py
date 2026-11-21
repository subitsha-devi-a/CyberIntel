
from modules.vector_rag import vector_search

question = "Which software has a remote code execution vulnerability?"

print("\nCYBERINTEL VECTOR RAG TEST")
print("--------------------------")

results = vector_search(question)

for item in results:
    print("\nTitle:", item["title"])
    print("Category:", item["category"])
    print("Similarity:", round(item["similarity"], 3))
    print("Information:", item["content"])
    print("Source:", item["source"])

print("\nVector RAG test completed.")
