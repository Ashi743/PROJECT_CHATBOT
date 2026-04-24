import time
import json
from langchain_core.tools import tool
from langchain_community.tools import DuckDuckGoSearchRun
from dotenv import load_dotenv
from .graders import (
    grade_document_relevance,
    generate_answer,
    check_hallucination,
    check_usefulness
)
from .retriever import retrieve_documents, save_document_to_chroma

load_dotenv()

web_search = DuckDuckGoSearchRun()


def unified_rag_pipeline(question: str) -> dict:
    """C-RAG + Self-RAG unified pipeline with ChromaDB retrieval"""
    max_loops = 3
    max_timeout = 30
    retrieval_count = 0
    generation_count = 0
    start_time = time.time()
    best_answer = None

    while retrieval_count + generation_count < max_loops:
        if time.time() - start_time > max_timeout:
            return {
                "answer": best_answer or "[TIMEOUT] Unable to generate answer within 30 seconds",
                "metrics": {
                    "retrieval_loops": retrieval_count,
                    "generation_retries": generation_count,
                    "total_loops": retrieval_count + generation_count,
                    "response_time": time.time() - start_time,
                    "timeout": True,
                    "success": False
                }
            }

        documents = retrieve_documents(question, k=4)

        relevant_documents = []
        for doc in documents:
            grade = grade_document_relevance(question, doc["content"])
            if grade == "yes":
                relevant_documents.append(doc)

        web_search_triggered = False
        if not relevant_documents:
            try:
                web_results = web_search.run(question)
                relevant_documents = [{"content": web_results[:500], "source": "web_search"}]
                web_search_triggered = True
            except Exception as e:
                return {
                    "answer": "[ERROR] Could not retrieve documents or search web",
                    "metrics": {
                        "retrieval_loops": retrieval_count,
                        "generation_retries": generation_count,
                        "total_loops": retrieval_count + generation_count,
                        "response_time": time.time() - start_time,
                        "success": False,
                        "error": str(e)
                    }
                }

        context = "\n\n".join([doc["content"] for doc in relevant_documents])[:2000]

        answer = generate_answer(question, context)
        best_answer = answer
        generation_count += 1

        docs_text = context
        hall_grade = check_hallucination(docs_text, answer)

        if hall_grade == "no":
            retrieval_count += 1
            continue

        use_grade = check_usefulness(question, answer)

        if use_grade == "no":
            generation_count += 1
            continue

        return {
            "answer": answer,
            "metrics": {
                "retrieval_loops": retrieval_count,
                "generation_retries": generation_count,
                "total_loops": retrieval_count + generation_count,
                "response_time": time.time() - start_time,
                "web_search_triggered": web_search_triggered,
                "success": True
            }
        }

    return {
        "answer": best_answer or "[FAILED] Unable to generate answer after max retries",
        "metrics": {
            "retrieval_loops": retrieval_count,
            "generation_retries": generation_count,
            "total_loops": retrieval_count + generation_count,
            "response_time": time.time() - start_time,
            "max_loops_exceeded": True,
            "success": False
        }
    }


@tool
def self_rag_query(question: str) -> str:
    """Query documents using C-RAG + Self-RAG with ChromaDB.

    Dual-layer quality control system:
    1. C-RAG: Document relevance grading (Prompt 1)
    2. RAG Generation: Answer from context (Prompt 2)
    3. Self-RAG: Hallucination check (Prompt 3)
    4. Self-RAG: Usefulness check (Prompt 4)

    Supports: PDF, Word (.docx, .doc), CSV, Excel files
    Web search fallback: DuckDuckGo (if no relevant documents)
    Vector database: ChromaDB

    Args:
        question: User's question (5-500 characters)

    Returns:
        str: Grounded answer with metrics
    """
    if not question or len(question.strip()) < 5:
        return "[ERROR] Question must be at least 5 characters long"

    result = unified_rag_pipeline(question.strip())
    answer = result.get("answer", "")
    metrics = result.get("metrics", {})

    response = f"{answer}\n\n[OK] Time: {metrics.get('response_time', 0):.2f}s | "
    response += f"Loops: {metrics.get('total_loops', 0)} | "
    response += f"Web: {'Yes' if metrics.get('web_search_triggered') else 'No'}"

    return response


if __name__ == "__main__":
    test_result = unified_rag_pipeline("What is machine learning?")
    print(json.dumps(test_result, indent=2))
