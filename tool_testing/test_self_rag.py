import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.RAG.self_rag_tool import self_rag_query, unified_rag_pipeline
from tools.RAG.retriever import save_document_to_chroma, get_indexed_documents

def test_rag_pipeline():
    print("[OK] Testing C-RAG + Self-RAG Pipeline\n")

    test_question = "What is machine learning?"

    print(f"Test Question: {test_question}\n")
    print("Running unified RAG pipeline...\n")

    try:
        result = unified_rag_pipeline(test_question)

        print(f"[OK] Pipeline completed")
        print(f"Answer: {result.get('answer', 'No answer')}\n")

        metrics = result.get("metrics", {})
        print("Metrics:")
        print(f"  - Response Time: {metrics.get('response_time', 0):.2f}s")
        print(f"  - Total Loops: {metrics.get('total_loops', 0)}")
        print(f"  - Retrieval Loops: {metrics.get('retrieval_loops', 0)}")
        print(f"  - Generation Retries: {metrics.get('generation_retries', 0)}")
        print(f"  - Web Search Triggered: {metrics.get('web_search_triggered', False)}")
        print(f"  - Success: {metrics.get('success', False)}\n")

    except Exception as e:
        print(f"[ERROR] {str(e)}\n")
        import traceback
        traceback.print_exc()


def test_rag_tool():
    print("[OK] Testing Self-RAG Tool\n")

    test_question = "What is retrieval-augmented generation?"

    print(f"Test Question: {test_question}\n")

    try:
        result = self_rag_query(test_question)
        print(f"[OK] Tool executed successfully\n")
        print(f"Result:\n{result}\n")

    except Exception as e:
        print(f"[ERROR] {str(e)}\n")
        import traceback
        traceback.print_exc()


def test_document_indexing():
    print("[OK] Testing Document Indexing\n")

    create_test_doc = False

    if create_test_doc:
        test_doc_path = "test_document.txt"
        with open(test_doc_path, "w") as f:
            f.write("""
Machine Learning is a subset of Artificial Intelligence that enables systems
to learn and improve from experience without being explicitly programmed.

Types of Machine Learning:
1. Supervised Learning: Learning from labeled data
2. Unsupervised Learning: Finding patterns in unlabeled data
3. Reinforcement Learning: Learning through trial and error

Applications include image recognition, natural language processing, and more.
            """)

        print(f"Created test document: {test_doc_path}")

        try:
            result = save_document_to_chroma(test_doc_path, "ML Introduction")
            print(f"[OK] {result['message']}")
            print(f"    Documents indexed: {result.get('doc_count', 0)}\n")
        except Exception as e:
            print(f"[ERROR] {str(e)}\n")

    try:
        docs = get_indexed_documents()
        print(f"[OK] Retrieved {len(docs)} indexed documents\n")

        if docs:
            print("Indexed Documents:")
            for doc in docs[:5]:
                print(f"  - {doc['name']} ({doc['source']})")
                print(f"    Preview: {doc['preview'][:60]}...\n")

    except Exception as e:
        print(f"[ERROR] {str(e)}\n")


if __name__ == "__main__":
    print("=" * 70)
    print("C-RAG + SELF-RAG TOOL TEST SUITE")
    print("=" * 70 + "\n")

    test_rag_pipeline()
    print("\n" + "=" * 70 + "\n")

    test_rag_tool()
    print("\n" + "=" * 70 + "\n")

    test_document_indexing()
    print("\n" + "=" * 70)
    print("[OK] All tests completed")
