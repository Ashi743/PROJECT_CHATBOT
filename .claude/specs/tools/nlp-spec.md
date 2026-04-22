# NLP Analysis Spec Sheet

## Purpose
Comprehensive NLP analysis: sentiment, keywords, extractive summary, named entities, language detection, text statistics.
Uses VADER sentiment + NLTK for parsing/NER + langdetect for language ID.

## Status
[DONE]

## Trigger Phrases
- "analyze the sentiment of this text"
- "extract keywords from the article"
- "summarize this document"
- "find named entities in the text"
- "what language is this"
- "analyze this market report"

## Input Parameters
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| text | str | yes | none | Text to analyze |
| task | str | no | all | Task type: sentiment, keywords, summary, entities, language, stats, all |

## Output Format
NLP Analysis Results:
==================================================

SENTIMENT:
  Overall: POSITIVE
  Positive: 65.2% | Negative: 12.3% | Neutral: 22.5%
  Compound Score: 0.692

KEYWORDS (127 unique):
  - wheat: 8x
  - price: 6x
  - market: 5x

SUMMARY (2/5 sentences):
  Wheat prices surged due to supply constraints. Market analysts expect volatility.

NAMED ENTITIES (12 found):
  PERSON: John Smith, Jane Doe
  ORG: USDA, CBOT
  LOCATION: USA, Brazil, Argentina

LANGUAGE: ENGLISH (confidence: 0.98)

TEXT STATISTICS:
  Characters: 5,234 (no spaces: 4,567)
  Words: 892 (unique: 412)
  Sentences: 23
  Avg Word Length: 5.12 chars
  Avg Sentence Length: 38.78 words

## Dependencies
- nltk (pip: nltk)
- langdetect (pip: langdetect)
- langchain_core.tools

## HITL
No - read-only analysis

## Chaining
Combines with:
- web_search → "search for wheat news and analyze sentiment"
- monitor_tool → "monitor commodity sentiment from market reports"

## Known Issues
- VADER optimized for social media, may under/over-estimate formal text sentiment
- NER uses English model only (single language)
- Stopwords/tokenization English-only by default
- Language detection fails on very short text (returns "unknown")

## Test Command
python -c "
from tools.nlp_tool import nlp_analyze
text = 'Wheat prices jumped today due to supply concerns.'
print(nlp_analyze.invoke({'text': text, 'task': 'all'}))
"

## Bunge Relevance
Market sentiment analysis for commodity prices, news monitoring, and trading decision support.

## Internal Notes
- VADER compound score: -1 (negative) to +1 (positive), threshold ±0.05
- Keyword extraction: TF-IDF-like frequency approach, removes stopwords
- Summary: extractive (selects existing sentences), top 3 by word frequency
- NER: uses averaged_perceptron_tagger + ne_chunk, binary=False for detailed types
- Language: returns top probability with confidence score
- Auto-downloads NLTK data on first run (quiet mode)
