from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, max_tokens=100)

def grade_document_relevance(question: str, document: str) -> str:
    """PROMPT 1: Document Relevance Grading [IsRel] — C-RAG LAYER"""
    prompt = f"""You are a relevance grader. Your job is to evaluate whether a retrieved
document is relevant to answering the user's question.

GRADING CRITERIA:
  - Is the document directly relevant to the question?
  - Does it contain useful information (not just tangentially related)?
  - Would including this document help answer the question?

Be STRICT, not lenient:
  - Vague or only partially related documents → score "no"
  - Only score "yes" if the document clearly helps

Respond with ONLY "yes" or "no". No explanation.

Question: {question}

Retrieved document:
{document}

Is this document relevant and useful for answering the question?"""

    response = llm.invoke(prompt)
    result = response.content.strip().lower()
    return "yes" if "yes" in result else "no"


def generate_answer(question: str, context: str) -> str:
    """PROMPT 2: Answer Generation"""
    prompt = f"""You are a helpful, accurate assistant. Answer using ONLY the provided context.

RULES:
  1. Use ONLY information from the context
  2. If context insufficient, say so clearly
  3. Be concise and direct
  4. When relevant, cite which part of context you're using
  5. Do NOT make up information or speculate

If you truly cannot answer from the context:
"I don't have enough information in the provided documents to answer this adequately."

Context:
{context}

Question: {question}

Answer:"""

    response = llm.invoke(prompt)
    return response.content.strip()


def check_hallucination(documents: str, generation: str) -> str:
    """PROMPT 3: Hallucination Check [IsSup] — SELF-RAG LAYER"""
    prompt = f"""You are a hallucination detector. Your job is to verify whether a generated
answer is grounded in the provided facts.

GRADING CRITERIA:
  - Read the facts provided in the documents
  - Read the generated answer
  - Check if EVERY claim in the answer can be traced back to the documents
  - If any claim contradicts or goes beyond the documents → hallucination

WHAT COUNTS AS HALLUCINATION:
  ✗ Invented statistics or numbers
  ✗ Unsupported conclusions
  ✗ Claims not mentioned in documents
  ✗ Speculation presented as fact

Be CRITICAL:
  - When in doubt, mark as hallucination
  - Better false positive than false negative

Respond with ONLY "yes" (grounded) or "no" (hallucination). No explanation.

Facts from documents:
{documents[:2000]}

Generated answer:
{generation}

Is this answer grounded in the facts?"""

    response = llm.invoke(prompt)
    result = response.content.strip().lower()
    return "yes" if "yes" in result else "no"


def check_usefulness(question: str, generation: str) -> str:
    """PROMPT 4: Usefulness Check [IsUse] — SELF-RAG LAYER"""
    prompt = f"""You are an answer quality grader. Your job is to assess whether a generated
answer adequately addresses the user's original question.

GRADING CRITERIA:
  - Does it directly answer what was asked?
  - Is it complete enough to be helpful?
  - Would a user be satisfied with this answer?

SCORE "no" IF:
  ✗ Answer is vague or incomplete
  ✗ It avoids the main question
  ✗ Provides irrelevant information instead

SCORE "yes" IF:
  ✓ Clearly addresses the question
  ✓ Provides concrete, useful information
  ✓ A user would find it helpful

Be STRICT on completeness.

Respond with ONLY "yes" or "no". No explanation.

Original question:
{question}

Generated answer:
{generation}

Does this answer adequately address the question?"""

    response = llm.invoke(prompt)
    result = response.content.strip().lower()
    return "yes" if "yes" in result else "no"
