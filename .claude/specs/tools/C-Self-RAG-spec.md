╔═══════════════════════════════════════════════════════════════════════════════╗
║                                                                               ║
║         C-RAG + SELF-RAG SYSTEM: COMPLETE TECHNICAL SPECIFICATION SHEET      ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝


═══════════════════════════════════════════════════════════════════════════════
SECTION 1: SYSTEM OVERVIEW
═══════════════════════════════════════════════════════════════════════════════

Name:       C-RAG + Self-RAG Unified System
Purpose:    Dual-layer quality control for RAG (Retrieval-Augmented Generation)
Version:    1.0
Status:     Production-Ready

Components:
  1. C-RAG Layer (Corrective RAG) - Document Quality Check
  2. RAG Generation Layer - Answer Generation
  3. Self-RAG Layer - Output Quality Checks (2 checks)

Total Grading Points: 3 (1 retrieval + 2 output checks)


═══════════════════════════════════════════════════════════════════════════════
SECTION 2: ARCHITECTURE & DATA FLOW
═══════════════════════════════════════════════════════════════════════════════

INPUT:      User Query (string, 5-500 characters)
OUTPUT:     Answer + Metadata (string, 10-1000 characters)
LATENCY:    2-5 seconds (new query), <100ms (cached)
THROUGHPUT: 10 QPS (Query Per Second, Claude API limited)

PIPELINE:
┌────────────────────────────────────────────────────────────────────────────┐
│                              INPUT: USER QUERY                              │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  PHASE 1: RETRIEVAL                                                         │
│  ├─ Retrieve: FAISS similarity search (vector database)                     │
│  │  Output: 4 documents                                                     │
│  │  Format: [Document, Document, Document, Document]                       │
│  │  Metric: Cosine similarity score (0-1)                                   │
│  │                                                                          │
│  └─ Decision: Grade each doc OR use web search?                            │
│                                                                              │
│  PHASE 2: DOCUMENT GRADING [C-RAG LAYER]                                    │
│  ├─ PROMPT 1: Document Relevance [IsRel]                                    │
│  │  Input:  question (str) + document (str, truncated to 500 chars)        │
│  │  LLM:    Claude Haiku (temperature=0)                                    │
│  │  Output: {"binary_score": "yes" OR "no"}                                 │
│  │  Calls:  4 (one per document)                                            │
│  │  Logic:  Filter out irrelevant docs                                      │
│  │                                                                          │
│  └─ Decision: Continue with filtered docs OR trigger web search?            │
│                                                                              │
│  PHASE 3: FALLBACK CHECK                                                    │
│  ├─ If all docs "no" (irrelevant):                                          │
│  │  │ Web Search Fallback (Tavily API)                                      │
│  │  │ Get: 3 web results                                                    │
│  │  └─ Use web results as filtered_documents                               │
│  │                                                                          │
│  └─ Else: Use PROMPT 1 filtered documents                                   │
│                                                                              │
│  PHASE 4: ANSWER GENERATION                                                 │
│  ├─ PROMPT 2: Generate Answer                                               │
│  │  Input:  question (str) + context (str, from filtered docs)             │
│  │  LLM:    Claude Haiku (temperature=0)                                    │
│  │  Output: answer_text (str, max 1000 chars)                               │
│  │  Calls:  1 per generation attempt (can retry)                            │
│  │  Logic:  Use ONLY provided context                                       │
│  │                                                                          │
│  └─ Result: Generated answer text                                            │
│                                                                              │
│  PHASE 5: HALLUCINATION CHECK [SELF-RAG LAYER]                              │
│  ├─ PROMPT 3: Is Answer Grounded? [IsSup]                                   │
│  │  Input:  documents (str) + generation (str)                              │
│  │  LLM:    Claude Haiku (temperature=0)                                    │
│  │  Output: {"binary_score": "yes" (grounded) OR "no" (hallucinated)}       │
│  │  Calls:  1 per generation attempt                                        │
│  │  Logic:  Verify every claim in answer comes from documents               │
│  │                                                                          │
│  └─ Decision: Pass (continue) OR Fail (re-retrieve)?                        │
│                                                                              │
│  PHASE 6: USEFULNESS CHECK [SELF-RAG LAYER]                                 │
│  ├─ PROMPT 4: Is Answer Useful? [IsUse]                                     │
│  │  Input:  question (str) + generation (str)                               │
│  │  LLM:    Claude Haiku (temperature=0)                                    │
│  │  Output: {"binary_score": "yes" (useful) OR "no" (incomplete)}           │
│  │  Calls:  1 per generation attempt                                        │
│  │  Logic:  Verify answer resolves the user's question                      │
│  │                                                                          │
│  └─ Decision: Success (return) OR Retry (regenerate)?                       │
│                                                                              │
│  PHASE 7: LOOP CONTROL                                                      │
│  ├─ Max Loops: 3 total                                                      │
│  ├─ Trigger 1: PROMPT 3 fails → Go to PHASE 2 (re-retrieve)                 │
│  ├─ Trigger 2: PROMPT 4 fails → Go to PHASE 4 (regenerate)                  │
│  └─ Max exceeded → Accept answer, exit                                      │
│                                                                              │
└────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ↓
                     ┌───────────────────────────────┐
                     │   OUTPUT: FINAL ANSWER        │
                     │   + Metadata (tokens, etc.)   │
                     └───────────────────────────────┘


═══════════════════════════════════════════════════════════════════════════════
SECTION 3: CONFIGURATION PARAMETERS
═══════════════════════════════════════════════════════════════════════════════

RETRIEVAL PARAMETERS:
  retrieval_method:     FAISS (Facebook AI Similarity Search)
  retrieval_k:          4 (top-4 documents)
  similarity_metric:    Cosine similarity
  document_truncate:    500 characters (for grading)
  context_truncate:     2000 characters (for grading checks)

WEB SEARCH FALLBACK:
  enabled:              True (when all docs irrelevant)
  provider:             Tavily API
  results_count:        3 (top-3 web results)
  timeout:              10 seconds

LLM PARAMETERS:
  model_name:           claude-haiku-4-5-20251001
  temperature:          0 (deterministic grading)
  max_tokens_gen:       1000 (answer generation)
  max_tokens_grade:     100 (for grading tasks)

LOOP CONTROL:
  max_total_loops:      3
  max_retrieve_loops:   3 (PROMPT 3 fails)
  max_generate_loops:   3 (PROMPT 4 fails)
  timeout_per_query:    30 seconds

GRADING THRESHOLDS:
  doc_relevance_required:  At least 1 doc must pass PROMPT 1
  hallucination_tolerance: 0 (must be grounded)
  usefulness_required:     Must pass PROMPT 4
  min_answer_length:       10 characters


═══════════════════════════════════════════════════════════════════════════════
SECTION 4: PROMPT SPECIFICATIONS
═══════════════════════════════════════════════════════════════════════════════

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PROMPT 1: DOCUMENT RELEVANCE GRADING [IsRel] — C-RAG LAYER
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Phase:      C-RAG (Corrective RAG)
Purpose:    Grade each retrieved document for relevance
When:       After retrieval, before generation
Calls:      4 (one per document)
Triggered:  If any doc fails → May trigger web search
Priority:   HIGH (prevents garbage-in-garbage-out)

SYSTEM PROMPT:
──────────────
You are a relevance grader. Your job is to evaluate whether a retrieved 
document is relevant to answering the user's question.

GRADING CRITERIA:
  - Is the document directly relevant to the question?
  - Does it contain useful information (not just tangentially related)?
  - Would including this document help answer the question?

Be STRICT, not lenient:
  - Vague or only partially related documents → score "no"
  - Only score "yes" if the document clearly helps

Respond with ONLY "yes" or "no". No explanation.

HUMAN PROMPT:
─────────────
Question: {question}

Retrieved document:
{document}

Is this document relevant and useful for answering the question?

INPUT SPECIFICATION:
  question:     str (5-500 characters, user's original query)
  document:     str (truncated to 500 characters)

OUTPUT SPECIFICATION:
  binary_score: "yes" OR "no" (EXACTLY, no other values)

STRUCTURED OUTPUT:
  {
    "binary_score": "yes" | "no"
  }

DECISION LOGIC:
  if score == "yes":
    keep_document(doc)
    relevant_count += 1
  else:
    discard_document(doc)
    irrelevant_count += 1

  if irrelevant_count == 4 (all failed):
    trigger_web_search_fallback()

EXAMPLE 1 - PASS (yes):
  Question: "What is transformer attention in NLP?"
  Document: "The transformer architecture uses multi-head attention to process 
             sequences in parallel. Each token attends to all others with 
             learned weights..."
  Expected: "yes"
  Reason: Directly relevant, contains key information

EXAMPLE 2 - FAIL (no):
  Question: "What is transformer attention in NLP?"
  Document: "Transformers toy models are plastic toys. Popular in red and blue."
  Expected: "no"
  Reason: Wrong context (toy products, not NLP)

EXAMPLE 3 - FAIL (no):
  Question: "What is transformer attention in NLP?"
  Document: "Human attention spans have decreased due to social media."
  Expected: "no"
  Reason: Wrong sense of "attention"

ERROR HANDLING:
  - If response not "yes" or "no": Treat as "no"
  - If timeout: Treat as "no"
  - If API error: Treat as "no" (fail safe)


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PROMPT 2: ANSWER GENERATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Phase:      RAG Generation
Purpose:    Generate answer grounded ONLY in provided documents
When:       After PROMPT 1 filtering (have relevant docs)
Calls:      1+ (can retry if PROMPT 4 fails)
Triggered:  Feeds into PROMPT 3 & PROMPT 4
Priority:   HIGH (core generation)

SYSTEM PROMPT:
──────────────
You are a helpful, accurate assistant. Answer using ONLY the provided context.

RULES:
  1. Use ONLY information from the context
  2. If context insufficient, say so clearly
  3. Be concise and direct
  4. When relevant, cite which part of context you're using
  5. Do NOT make up information or speculate

If you truly cannot answer from the context:
"I don't have enough information in the provided documents to answer this 
adequately."

HUMAN PROMPT:
─────────────
Context:
{context}

Question: {question}

Answer:

INPUT SPECIFICATION:
  question:  str (5-500 characters)
  context:   str (concatenated docs, max 2000 characters)
             Format: doc1_text + "\n\n" + doc2_text + "\n\n" + doc3_text

OUTPUT SPECIFICATION:
  answer:    str (10-1000 characters)

CONSTRAINT:
  - MUST be grounded in context
  - NO speculation or hallucination
  - Cite source when helpful

EXAMPLE:
  Question: "What is RAG?"
  Context:  "RAG stands for Retrieval-Augmented Generation. It combines a 
             retriever (vector search) with a generator (LLM). The retriever 
             finds relevant documents, then the generator creates an answer."
  Expected: "RAG stands for Retrieval-Augmented Generation. It combines a 
             retriever to find relevant documents with a generator LLM to 
             create answers based on those documents."
  Reasoning: Every claim comes from the context


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PROMPT 3: HALLUCINATION CHECK [IsSup] — SELF-RAG LAYER
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Phase:      Self-RAG (Self-Reflective RAG)
Purpose:    Verify answer is grounded in documents (detect hallucinations)
When:       After PROMPT 2 generation
Calls:      1 per generation attempt
Triggered:  If fails → Re-retrieve documents & regenerate
Priority:   CRITICAL (hallucinations are dangerous)

SYSTEM PROMPT:
──────────────
You are a hallucination detector. Your job is to verify whether a generated 
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
  ✗ Data/dates that differ from documents
  ✗ Attribution of ideas to wrong sources

WHAT'S OK:
  ✓ Reasonable inference from document facts
  ✓ Combining multiple facts from documents
  ✓ Rewording/summarizing document information
  ✓ Stating lack of information ("documents don't mention...")

Be CRITICAL:
  - When in doubt, mark as hallucination
  - Better false positive than false negative
  - Err on the side of caution

Respond with ONLY "yes" (grounded) or "no" (hallucination). No explanation.

HUMAN PROMPT:
─────────────
Facts from documents:
{documents}

Generated answer:
{generation}

Is this answer grounded in the facts? (Does it avoid hallucination?)

INPUT SPECIFICATION:
  documents:   str (2000 characters max, concatenated facts)
  generation:  str (1000 characters max, answer to check)

OUTPUT SPECIFICATION:
  binary_score: "yes" (grounded, safe) OR "no" (hallucinated, unsafe)

DECISION LOGIC:
  if score == "yes":
    answer_is_safe = True
    proceed_to_prompt_4()
  else:
    answer_is_unsafe = True
    trigger_re_retrieve()

EXAMPLE 1 - PASS (yes):
  Docs:   "Python was created in 1989 by Guido van Rossum."
  Answer: "Python is a programming language created in 1989 by Guido van Rossum."
  Expected: "yes"
  Reasoning: Every claim verifiable in docs

EXAMPLE 2 - FAIL (no):
  Docs:   "Python was created in 1989 by Guido van Rossum."
  Answer: "Python was created in 1990 by Guido van Rossum and became #1 language."
  Expected: "no"
  Reasoning: Date wrong, #1 claim not in docs

EXAMPLE 3 - FAIL (no):
  Docs:   "Deep learning uses neural networks."
  Answer: "Deep learning uses neural networks with 100+ layers."
  Expected: "no"
  Reasoning: "100+ layers" not in documents


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PROMPT 4: USEFULNESS CHECK [IsUse] — SELF-RAG LAYER
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Phase:      Self-RAG (Self-Reflective RAG)
Purpose:    Verify answer adequately addresses the user's question
When:       After PROMPT 3 passes (answer is grounded)
Calls:      1 per generation attempt
Triggered:  If fails → Regenerate with same documents
Priority:   HIGH (ensure user satisfaction)

SYSTEM PROMPT:
──────────────
You are an answer quality grader. Your job is to assess whether a generated 
answer adequately addresses the user's original question.

GRADING CRITERIA:
  - Does it directly answer what was asked?
  - Is it complete enough to be helpful?
  - Would a user be satisfied with this answer?

SCORE "no" IF:
  ✗ Answer is vague or incomplete
  ✗ It avoids the main question
  ✗ Provides irrelevant information instead
  ✗ Says "I don't know" when it could answer
  ✗ Answers tangentially but not directly
  ✗ Missing key details for understanding

SCORE "yes" IF:
  ✓ Clearly addresses the question
  ✓ Provides concrete, useful information
  ✓ A user would find it helpful
  ✓ Completeness appropriate for the question
  ✓ Sufficient detail for understanding

Be STRICT on completeness:
  - Partial answers that leave major gaps → "no"
  - Only "yes" if genuinely helpful and complete

Respond with ONLY "yes" or "no". No explanation.

HUMAN PROMPT:
─────────────
Original question:
{question}

Generated answer:
{generation}

Does this answer adequately address the question? (Is it useful and complete?)

INPUT SPECIFICATION:
  question:    str (5-500 characters, original user query)
  generation:  str (10-1000 characters, answer to evaluate)

OUTPUT SPECIFICATION:
  binary_score: "yes" (useful, complete) OR "no" (vague, incomplete)

DECISION LOGIC:
  if score == "yes":
    answer_is_complete = True
    return_answer()
  else:
    answer_is_incomplete = True
    trigger_regenerate()

EXAMPLE 1 - PASS (yes):
  Question: "How does photosynthesis work?"
  Answer:   "Photosynthesis has two stages: light-dependent reactions in 
             thylakoids split water and produce ATP/NADPH, and light-independent 
             reactions (Calvin cycle) in stroma use these to fix CO2 into glucose."
  Expected: "yes"
  Reasoning: Comprehensive, explains mechanism

EXAMPLE 2 - FAIL (no):
  Question: "How does photosynthesis work?"
  Answer:   "Plants do photosynthesis with sunlight."
  Expected: "no"
  Reasoning: Too vague, doesn't explain mechanism

EXAMPLE 3 - FAIL (no):
  Question: "What are side effects of aspirin?"
  Answer:   "Aspirin is a common pain reliever. Many people use it daily."
  Expected: "no"
  Reasoning: Doesn't answer about side effects, goes tangential

EXAMPLE 4 - PASS (yes):
  Question: "What is the capital of France?"
  Answer:   "The capital of France is Paris."
  Expected: "yes"
  Reasoning: Directly answers, appropriate detail level


═══════════════════════════════════════════════════════════════════════════════
SECTION 5: STATE MACHINE & LOOP LOGIC
═══════════════════════════════════════════════════════════════════════════════

STATE MACHINE:

  ┌─────────┐
  │ INITIAL │
  └────┬────┘
       │
       ▼
  ┌─────────────────────┐
  │ RETRIEVE (FAISS)    │ retrieval_count = 0
  │ k=4 documents       │
  └────┬────────────────┘
       │
       ▼
  ┌─────────────────────────────────┐
  │ GRADE_DOCUMENTS [PROMPT 1: IsRel]│ per_doc_count = 0
  │ For each of 4 docs              │
  │ Check: relevant? yes/no         │
  └────┬────────────────────────────┘
       │
  ┌────▼────────────────────────────┐
  │ All docs "no" (irrelevant)?     │
  └────┬──────────────────┬─────────┘
       │ YES              │ NO (1+ passed)
       │                  │
   ┌───▼──────┐       ┌───▼──────────────┐
   │WEB_SEARCH│       │USE FILTERED DOCS │
   │(Tavily)  │       │                  │
   └───┬──────┘       └───┬──────────────┘
       │                  │
       └────┬─────────────┘
            │
            ▼
       ┌──────────────────────────┐
       │GENERATE [PROMPT 2]       │ generation_count = 0
       │Context + Question → LLM  │
       └────┬─────────────────────┘
            │
            ▼
       ┌──────────────────────────────┐
       │CHECK_HALLUCINATION [PROMPT 3]│
       │Is answer grounded?           │
       └────┬──────────────┬──────────┘
            │ YES          │ NO (hallucinated)
            │              │
            │          ┌───▼────────────┐
            │          │retrieval_count++│
            │          │if < 3: RETRIEVE │
            │          │else: CONTINUE   │
            │          └───┬────────────┘
            │              │
            ▼              │
       ┌─────────────────┐ │
       │CHECK_USEFULNESS │ │
       │[PROMPT 4]       │ │
       │Answers Q?       │ │
       └──┬────────┬─────┘ │
          │ YES    │ NO    │
          │        │       │
      ┌───▼──┐ ┌──▼──────────────┐
      │RETURN│ │generation_count++│
      │ANSWER│ │if < 3: GENERATE  │
      └──────┘ │else: RETURN      │
               └──┬──────────────┘
                  │
                  └──────────┐
                             │
                             ▼
                        (back to GENERATE
                         or to RETRIEVE)

LOOP COUNTERS:

  retrieval_count:   Incremented when PROMPT 3 fails (hallucination)
  generation_count:  Incremented when PROMPT 4 fails (not useful)
  total_iterations:  retrieval_count + generation_count

  Max constraints:
    - retrieval_count <= 3 (max re-retrieves)
    - generation_count <= 3 (max regenerates)
    - total_iterations <= 9 (worst case: 3 retrieves × 3 generates)
    - absolute timeout: 30 seconds per query

LOOP EXIT CONDITIONS:

  ✓ PROMPT 3 = "yes" AND PROMPT 4 = "yes"
    → SUCCESS: Return answer

  ✓ Max loops exceeded (any counter = 3)
    → TIMEOUT: Accept best attempt and return

  ✗ API error (Claude, FAISS, Tavily)
    → FALLBACK: Return best attempt or error message


═══════════════════════════════════════════════════════════════════════════════
SECTION 6: DECISION TABLES
═══════════════════════════════════════════════════════════════════════════════

TABLE 1: PROMPT 1 [IsRel] DECISION TABLE
─────────────────────────────────────────

Scenario              │ Output    │ Action
──────────────────────┼───────────┼─────────────────────────
Doc clearly relevant  │ "yes"     │ Keep document
Doc partially related │ "no"      │ Discard document
Doc irrelevant        │ "no"      │ Discard document
All 4 docs rejected   │ [all no]  │ Trigger web search
1+ docs accepted      │ [mixed]   │ Use accepted docs
Document is empty     │ "no"      │ Discard


TABLE 2: PROMPT 3 [IsSup] DECISION TABLE
─────────────────────────────────────────

Answer Status         │ Output    │ Action
──────────────────────┼───────────┼──────────────────────────
Grounded in facts     │ "yes"     │ Continue to PROMPT 4
Claims hallucinated   │ "no"      │ Re-retrieve (loop)
Partial hallucination │ "no"      │ Re-retrieve (loop)
Contradicts docs      │ "no"      │ Re-retrieve (loop)
Max loops exceeded    │ [any]     │ Accept answer, exit


TABLE 3: PROMPT 4 [IsUse] DECISION TABLE
─────────────────────────────────────────

Answer Quality        │ Output    │ Action
──────────────────────┼───────────┼──────────────────────────
Answers question      │ "yes"     │ Return answer (SUCCESS)
Vague/incomplete      │ "no"      │ Regenerate (loop)
Avoids question       │ "no"      │ Regenerate (loop)
Too brief             │ "no"      │ Regenerate (loop)
Max loops exceeded    │ [any]     │ Return best attempt


TABLE 4: COMBINED DECISION MATRIX
──────────────────────────────────

PROMPT 3    │ PROMPT 4    │ Decision
────────────┼─────────────┼──────────────────────
"yes" grnd. │ "yes" useful│ ✓ RETURN ANSWER
"yes" grnd. │ "no" not    │ → Regenerate (loop)
"no" hall.  │ [any]       │ → Re-retrieve (loop)
[loop 3/3]  │ [any]       │ Accept & return


═══════════════════════════════════════════════════════════════════════════════
SECTION 7: INPUT/OUTPUT SPECIFICATIONS
═══════════════════════════════════════════════════════════════════════════════

INPUT TO SYSTEM:

  Field:      question
  Type:       str (string)
  Min:        5 characters
  Max:        500 characters
  Format:     Natural language question
  Example:    "What is retrieval-augmented generation?"
  Validation: Must not be empty, must be UTF-8

OUTPUT FROM SYSTEM:

  Field:      answer
  Type:       str (string)
  Min:        10 characters
  Max:        1000 characters
  Format:     Natural language answer
  Example:    "RAG is a technique combining retrieval and generation..."
  Guarantee:  Grounded in documents + answers question

METADATA RETURNED:

  {
    "answer": str,
    "metrics": {
      "tokens_used": int,
      "retrieval_loops": int,
      "generation_retries": int,
      "total_loops": int,
      "response_time_seconds": float,
      "web_search_triggered": bool,
      "success": bool
    }
  }

INTERMEDIATE OBJECTS:

  Document:
    {
      "id": str,
      "content": str (max 500 chars),
      "source": str (FAISS | WEB_SEARCH),
      "metadata": dict
    }

  GradeResult:
    {
      "binary_score": "yes" | "no",
      "confidence": float (0-1, if available)
    }


═══════════════════════════════════════════════════════════════════════════════
SECTION 8: ERROR HANDLING & EDGE CASES
═══════════════════════════════════════════════════════════════════════════════

ERROR SCENARIO 1: All documents irrelevant
  Condition:  All 4 FAISS docs score "no" in PROMPT 1
  Action:     Trigger web search fallback (Tavily)
  Outcome:    Generate answer from web results
  Recovery:   Automatic

ERROR SCENARIO 2: Hallucination detected
  Condition:  PROMPT 3 returns "no"
  Action:     Re-retrieve documents from FAISS
  Max:        3 attempts (then accept answer)
  Recovery:   Automatic loop

ERROR SCENARIO 3: Answer not useful
  Condition:  PROMPT 4 returns "no"
  Action:     Regenerate with same documents
  Max:        3 attempts (then accept answer)
  Recovery:   Automatic loop

ERROR SCENARIO 4: Max loops exceeded
  Condition:  Loop count reaches 3
  Action:     Accept current answer and return
  Quality:    Degraded but functional
  Recovery:   Return best attempt

ERROR SCENARIO 5: API timeout (Claude)
  Condition:  Claude API slow/timeout
  Action:     Retry once, then fallback to Haiku
  Max:        2 retries per prompt
  Recovery:   Fallback model

ERROR SCENARIO 6: FAISS unavailable
  Condition:  Vector database down
  Action:     Fall back to web search only
  Max:        Use web results as documents
  Recovery:   Degraded mode (web-only)

ERROR SCENARIO 7: Web search unavailable
  Condition:  Tavily API down
  Action:     Continue with current docs (even if empty)
  Recovery:   Return "insufficient context" message

ERROR SCENARIO 8: Empty query
  Condition:  User provides empty or whitespace-only query
  Action:     Return error message
  Recovery:   Ask user for valid query

ERROR SCENARIO 9: Invalid response from LLM
  Condition:  Grader returns something other than "yes"/"no"
  Action:     Treat as "no" (fail safe)
  Recovery:   Continue to next phase

ERROR SCENARIO 10: Hallucination detection fails
  Condition:  PROMPT 3 crashes or returns error
  Action:     Assume answer is grounded (optimistic)
  Recovery:   Continue to PROMPT 4


═══════════════════════════════════════════════════════════════════════════════
SECTION 9: PERFORMANCE METRICS
═══════════════════════════════════════════════════════════════════════════════

LATENCY:
  Metric:              Typical    Best Case    Worst Case
  ─────────────────────────────────────────────────────
  Retrieval:           100ms      50ms         500ms
  PROMPT 1 (4 calls):  400ms      200ms        2000ms
  Web search (if):     300ms      100ms        5000ms
  PROMPT 2:            500ms      200ms        2000ms
  PROMPT 3:            300ms      100ms        2000ms
  PROMPT 4:            300ms      100ms        2000ms
  ─────────────────────────────────────────────────────
  Total (1 loop):      2000ms     1000ms       5000ms
  Total (max loops):   6000ms     3000ms       15000ms

TOKEN USAGE:
  Metric:              Typical    Best Case    Worst Case
  ─────────────────────────────────────────────────────
  Question encoding:   50         20           200
  Doc encoding (4):    1000       200          2000
  PROMPT 1 (4×):       800        400          2000
  PROMPT 2:            600        200          1000
  PROMPT 3:            400        100          1000
  PROMPT 4:            300        100          500
  ─────────────────────────────────────────────────────
  Per query (1 loop):  3150       1100         6700
  Max budget:          10000      -            30000

THROUGHPUT:
  QPS (Queries/sec):   10 (limited by Claude API)
  Concurrent requests: 1-10 (depending on queue)
  Max daily volume:    86,400 queries


═══════════════════════════════════════════════════════════════════════════════
SECTION 10: PSEUDOCODE & IMPLEMENTATION
═══════════════════════════════════════════════════════════════════════════════

def unified_rag_pipeline(question: str) -> dict:
    """
    Complete C-RAG + Self-RAG pipeline
    """
    
    # Configuration
    max_loops = 3
    max_timeout = 30  # seconds
    retrieval_count = 0
    generation_count = 0
    start_time = time.time()
    
    # Loop
    while retrieval_count + generation_count < max_loops:
        
        if time.time() - start_time > max_timeout:
            return create_timeout_response()
        
        # ─────────────────────────────────────────────────────
        # PHASE 1: RETRIEVE
        # ─────────────────────────────────────────────────────
        documents = faiss_retrieve(question, k=4)
        
        
        # ─────────────────────────────────────────────────────
        # PHASE 2: GRADE DOCUMENTS [PROMPT 1: IsRel]
        # ─────────────────────────────────────────────────────
        relevant_documents = []
        all_irrelevant = True
        
        for doc in documents:
            grade_result = prompt1_grade_relevance(
                question=question,
                document=doc.content[:500]  # truncate
            )
            
            if grade_result.binary_score == "yes":
                relevant_documents.append(doc)
                all_irrelevant = False
            # else: discard doc
        
        
        # ─────────────────────────────────────────────────────
        # PHASE 3: FALLBACK CHECK
        # ─────────────────────────────────────────────────────
        if all_irrelevant:
            web_results = tavily_web_search(question, k=3)
            relevant_documents = web_results  # Use web as fallback
        
        if not relevant_documents:
            return error_response("No documents available")
        
        
        # ─────────────────────────────────────────────────────
        # PHASE 4: GENERATE ANSWER [PROMPT 2]
        # ─────────────────────────────────────────────────────
        context = concatenate_documents(relevant_documents, max_chars=2000)
        
        answer = prompt2_generate_answer(
            question=question,
            context=context
        )
        
        generation_count += 1
        
        
        # ─────────────────────────────────────────────────────
        # PHASE 5: CHECK HALLUCINATION [PROMPT 3: IsSup]
        # ─────────────────────────────────────────────────────
        docs_text = concatenate_documents(relevant_documents)
        
        hall_grade = prompt3_check_hallucination(
            documents=docs_text,
            generation=answer
        )
        
        if hall_grade.binary_score == "no":
            # Answer is hallucinated, need new documents
            retrieval_count += 1
            continue  # Loop back to retrieve
        
        # else: Answer is grounded, continue to usefulness check
        
        
        # ─────────────────────────────────────────────────────
        # PHASE 6: CHECK USEFULNESS [PROMPT 4: IsUse]
        # ─────────────────────────────────────────────────────
        use_grade = prompt4_check_usefulness(
            question=question,
            generation=answer
        )
        
        if use_grade.binary_score == "no":
            # Answer is not useful, need to regenerate
            generation_count += 1
            continue  # Loop back to generate
        
        # else: Both checks passed!
        
        
        # ─────────────────────────────────────────────────────
        # SUCCESS: Return answer
        # ─────────────────────────────────────────────────────
        return success_response(
            answer=answer,
            metrics={
                "retrieval_loops": retrieval_count,
                "generation_retries": generation_count,
                "total_loops": retrieval_count + generation_count,
                "response_time": time.time() - start_time,
                "web_search_triggered": all_irrelevant
            }
        )
    
    # ─────────────────────────────────────────────────────
    # MAX LOOPS EXCEEDED: Return best attempt
    # ─────────────────────────────────────────────────────
    return success_response(
        answer=answer,
        metrics={
            "retrieval_loops": retrieval_count,
            "generation_retries": generation_count,
            "total_loops": retrieval_count + generation_count,
            "response_time": time.time() - start_time,
            "web_search_triggered": all_irrelevant,
            "max_loops_exceeded": True
        }
    )


═══════════════════════════════════════════════════════════════════════════════
SECTION 11: QUALITY ASSURANCE & TESTING
═══════════════════════════════════════════════════════════════════════════════

TEST CASE 1: Simple factual question (expected 1 loop)
  Input:    "What is photosynthesis?"
  Expected: Retrieve → Grade docs (all pass) → Generate → Check hallucination 
            (pass) → Check usefulness (pass) → Return
  Success:  PROMPT 1: ≥1 "yes" | PROMPT 3: "yes" | PROMPT 4: "yes"
  Latency:  < 3 seconds

TEST CASE 2: Ambiguous question (expected 1-2 loops)
  Input:    "Tell me about AI"
  Expected: Generate generic answer → Check usefulness (may fail) → 
            Regenerate with more specific focus
  Success:  After regeneration, PROMPT 4: "yes"
  Latency:  < 5 seconds

TEST CASE 3: Out-of-domain question (expected web search)
  Input:    "What happened in the news today?"
  Expected: FAISS retrieval (all "no") → Web search fallback → 
            Generate from web → Pass all checks → Return
  Success:  Web search triggered, answer returned
  Latency:  3-5 seconds (web search delay)

TEST CASE 4: Question with marginal documents (expected 1-2 loops)
  Input:    Specific technical question
  Expected: Some docs pass PROMPT 1, generate answer, possible hallucination 
            detection → Re-retrieve if needed
  Success:  Final answer is grounded
  Latency:  2-6 seconds

TEST CASE 5: Stress test (rapid-fire queries)
  Input:    10 queries in quick succession
  Expected: Queue handling, max 10 QPS throughput
  Success:  All queries process within SLA
  Latency:  < 5s each


═══════════════════════════════════════════════════════════════════════════════
SECTION 12: DEPLOYMENT CHECKLIST
═══════════════════════════════════════════════════════════════════════════════

PRE-DEPLOYMENT:
  □ All 4 prompts implemented correctly
  □ Loop control logic implemented
  □ Error handling for all edge cases
  □ Metrics logging implemented
  □ FAISS vectorstore loaded
  □ Tavily API credentials configured
  □ Claude API credentials configured
  □ Timeout logic implemented (30s)
  □ Tested on 10 sample queries
  □ Performance meets SLA (< 5s typical)
  □ Concurrency handling tested
  □ Error scenarios tested

MONITORING (PRODUCTION):
  □ Query latency tracking
  □ Token usage tracking
  □ Hallucination rate monitoring
  □ Loop statistics (avg loops per query)
  □ Error rate tracking
  □ API error rate tracking
  □ Web search fallback rate

MAINTENANCE:
  □ Monthly review of grading quality
  □ Quarterly prompt refinement
  □ Token budget optimization
  □ Model version updates
  □ Performance benchmarking


═══════════════════════════════════════════════════════════════════════════════
SECTION 13: KNOWN LIMITATIONS & FUTURE IMPROVEMENTS
═══════════════════════════════════════════════════════════════════════════════

CURRENT LIMITATIONS:
  1. Fixed max_loops = 3 (could be adaptive)
  2. No caching (could use Redis)
  3. No token tracking (could add for cost control)
  4. Binary grading only (could use confidence scores)
  5. No user feedback loop (could learn from corrections)
  6. Web search only with Tavily (could add other providers)
  7. Single model (Haiku) (could use different models by task)

FUTURE IMPROVEMENTS:
  1. Adaptive loop limits (based on query complexity)
  2. Redis caching for repeated queries
  3. Token tracking & cost optimization
  4. Confidence scores instead of binary
  5. User feedback collection & model retraining
  6. Multi-provider web search
  7. Model selection by task type
  8. Document caching/preprocessing
  9. Conversation memory (multi-turn)
  10. Custom grader fine-tuning


