from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import re

load_dotenv()

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, max_completion_tokens=50)
answer_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, max_completion_tokens=500)

def grade_document_relevance(question: str, document: str) -> str:
    """PROMPT 1: Document Relevance Grading [IsRel] — C-RAG LAYER"""
    prompt = f"""Answer with ONLY "yes" or "no". Nothing else.

Question: {question}

Document: {document[:300]}

Is this document relevant?"""

    response = llm.invoke(prompt)
    if isinstance(response.content, str):
        result = response.content.strip().lower()
    else:
        result = str(response.content).strip().lower()

    return "yes" if result.startswith("yes") else "no"


def generate_answer(question: str, context: str) -> str:
    """PROMPT 2: Answer Generation"""
    prompt = f"""Answer using ONLY the provided context. Be direct and clear.

Context:
{context}

Question: {question}

Answer:"""

    response = answer_llm.invoke(prompt)
    if isinstance(response.content, str):
        answer = response.content.strip()
    else:
        answer = str(response.content).strip()

    answer = re.sub(r'\b(yes|no)\b\s*', '', answer, flags=re.IGNORECASE).strip()
    return answer if answer else "I don't have enough information in the provided documents to answer this adequately."


def check_hallucination(documents: str, generation: str) -> str:
    """PROMPT 3: Hallucination Check [IsSup] — SELF-RAG LAYER"""
    prompt = f"""Is this answer grounded in the facts? Answer "yes" or "no" only.

Facts: {documents[:300]}

Answer: {generation[:300]}

Grounded?"""

    response = llm.invoke(prompt)
    if isinstance(response.content, str):
        result = response.content.strip().lower()
    else:
        result = str(response.content).strip().lower()
    return "yes" if result.startswith("yes") else "no"


def check_usefulness(question: str, generation: str) -> str:
    """PROMPT 4: Usefulness Check [IsUse] — SELF-RAG LAYER"""
    prompt = f"""Does this answer adequately address the question? Answer "yes" or "no" only.

Question: {question}

Answer: {generation[:300]}

Adequate?"""

    response = llm.invoke(prompt)
    if isinstance(response.content, str):
        result = response.content.strip().lower()
    else:
        result = str(response.content).strip().lower()
    return "yes" if result.startswith("yes") else "no"
