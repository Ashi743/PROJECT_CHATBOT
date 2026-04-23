from langchain_core.tools import tool
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
from nltk.corpus import stopwords
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.probability import FreqDist
import warnings

warnings.filterwarnings('ignore', category=DeprecationWarning)

# Download NLTK data quietly
nltk.download('vader_lexicon', quiet=True)
nltk.download('punkt', quiet=True)
nltk.download('punkt_tab', quiet=True)
nltk.download('stopwords', quiet=True)
nltk.download('averaged_perceptron_tagger', quiet=True)
nltk.download('averaged_perceptron_tagger_eng', quiet=True)
nltk.download('maxent_ne_chunker', quiet=True)
nltk.download('maxent_ne_chunker_tab', quiet=True)
nltk.download('words', quiet=True)
nltk.download('omw-1.4', quiet=True)

from langdetect import detect, detect_langs
import re


def _sentiment_analysis(text: str) -> dict:
    """Analyze sentiment using VADER"""
    sia = SentimentIntensityAnalyzer()
    scores = sia.polarity_scores(text)

    sentiment = "neutral"
    if scores['compound'] >= 0.05:
        sentiment = "positive"
    elif scores['compound'] <= -0.05:
        sentiment = "negative"

    return {
        "sentiment": sentiment,
        "positive": round(scores['pos'], 3),
        "negative": round(scores['neg'], 3),
        "neutral": round(scores['neu'], 3),
        "compound": round(scores['compound'], 3)
    }


def _keyword_extraction(text: str, top_k: int = 10) -> dict:
    """Extract keywords using TF-IDF-like approach"""
    sentences = sent_tokenize(text)
    words = word_tokenize(text.lower())

    # Remove stopwords and non-alphanumeric
    stop_words = set(stopwords.words('english'))
    words = [w for w in words if w.isalnum() and w not in stop_words and len(w) > 2]

    if not words:
        return {"keywords": [], "count": 0}

    freq_dist = FreqDist(words)
    top_keywords = freq_dist.most_common(top_k)

    return {
        "keywords": [{"word": word, "frequency": count} for word, count in top_keywords],
        "count": len(set(words))
    }


def _extractive_summary(text: str, num_sentences: int = 3) -> dict:
    """Generate extractive summary"""
    sentences = sent_tokenize(text)

    if len(sentences) <= num_sentences:
        return {
            "summary": text,
            "sentences_selected": len(sentences),
            "original_sentences": len(sentences)
        }

    # Score sentences by word frequency
    words = word_tokenize(text.lower())
    stop_words = set(stopwords.words('english'))
    words = [w for w in words if w.isalnum() and w not in stop_words]

    freq_dist = FreqDist(words)

    sent_scores = {}
    for i, sent in enumerate(sentences):
        words_in_sent = word_tokenize(sent.lower())
        score = sum(freq_dist[w] for w in words_in_sent if w in freq_dist)
        sent_scores[i] = score

    # Get top sentences in original order
    top_sent_indices = sorted(
        sorted(sent_scores.keys(), key=lambda x: sent_scores[x], reverse=True)[:num_sentences]
    )

    summary = " ".join([sentences[i] for i in top_sent_indices])

    return {
        "summary": summary,
        "sentences_selected": len(top_sent_indices),
        "original_sentences": len(sentences)
    }


def _ner_extraction(text: str) -> dict:
    """Extract named entities"""
    sentences = sent_tokenize(text)
    entities = {"PERSON": [], "ORG": [], "LOCATION": [], "OTHER": []}

    for sent in sentences:
        words = word_tokenize(sent)
        pos_tags = nltk.pos_tag(words)
        chunks = nltk.ne_chunk(pos_tags, binary=False)

        for chunk in chunks:
            if hasattr(chunk, 'label'):
                entity_text = " ".join(word for word, tag in chunk.leaves())
                entity_type = chunk.label()

                if entity_type in entities:
                    if entity_text not in entities[entity_type]:
                        entities[entity_type].append(entity_text)
                else:
                    if entity_text not in entities["OTHER"]:
                        entities["OTHER"].append(entity_text)

    return {
        "entities": {k: v for k, v in entities.items() if v},
        "total_entities": sum(len(v) for v in entities.values())
    }


def _language_detection(text: str) -> dict:
    """Detect language"""
    try:
        lang = detect(text)
        probs = detect_langs(text)

        lang_probs = {str(p).split(':')[0]: float(str(p).split(':')[1]) for p in probs}

        return {
            "language": lang,
            "confidence": round(max(lang_probs.values()), 3),
            "probabilities": {k: round(v, 3) for k, v in lang_probs.items()}
        }
    except:
        return {
            "language": "unknown",
            "confidence": 0,
            "probabilities": {}
        }


def _text_statistics(text: str) -> dict:
    """Calculate text statistics"""
    sentences = sent_tokenize(text)
    words = word_tokenize(text)
    chars = len(text)
    chars_no_space = len(text.replace(" ", ""))

    avg_word_len = sum(len(w) for w in words) / len(words) if words else 0
    avg_sent_len = len(words) / len(sentences) if sentences else 0

    return {
        "characters": chars,
        "characters_no_spaces": chars_no_space,
        "words": len(words),
        "sentences": len(sentences),
        "avg_word_length": round(avg_word_len, 2),
        "avg_sentence_length": round(avg_sent_len, 2),
        "unique_words": len(set(w.lower() for w in words if w.isalnum()))
    }


@tool
def nlp_analyze(text: str, task: str = "all") -> str:
    """
    Perform NLP analysis on text including sentiment, keywords, summary, NER, language, and stats.

    Args:
        text: The text to analyze
        task: Type of analysis - 'sentiment', 'keywords', 'summary', 'entities', 'language', 'stats', or 'all'

    Returns:
        Formatted string with analysis results
    """
    if not text or not text.strip():
        return "[ERROR] Empty text provided for analysis"

    results = {}
    task = task.lower().strip()

    try:
        if task in ['all', 'sentiment']:
            results['sentiment'] = _sentiment_analysis(text)

        if task in ['all', 'keywords']:
            results['keywords'] = _keyword_extraction(text)

        if task in ['all', 'summary']:
            results['summary'] = _extractive_summary(text)

        if task in ['all', 'entities']:
            results['entities'] = _ner_extraction(text)

        if task in ['all', 'language']:
            results['language'] = _language_detection(text)

        if task in ['all', 'stats']:
            results['stats'] = _text_statistics(text)

        # Format output
        output = "NLP Analysis Results:\n"
        output += "=" * 50 + "\n\n"

        if 'sentiment' in results:
            s = results['sentiment']
            output += f"SENTIMENT:\n"
            output += f"  Overall: {s['sentiment'].upper()}\n"
            output += f"  Positive: {s['positive']:.1%} | Negative: {s['negative']:.1%} | Neutral: {s['neutral']:.1%}\n"
            output += f"  Compound Score: {s['compound']}\n\n"

        if 'keywords' in results:
            k = results['keywords']
            output += f"KEYWORDS ({k['count']} unique):\n"
            for keyword in k['keywords'][:5]:
                output += f"  - {keyword['word']}: {keyword['frequency']}x\n"
            output += "\n"

        if 'summary' in results:
            sum_result = results['summary']
            output += f"SUMMARY ({sum_result['sentences_selected']}/{sum_result['original_sentences']} sentences):\n"
            output += f"  {sum_result['summary']}\n\n"

        if 'entities' in results:
            ent = results['entities']
            output += f"NAMED ENTITIES ({ent['total_entities']} found):\n"
            for entity_type, items in ent['entities'].items():
                output += f"  {entity_type}: {', '.join(items[:3])}\n"
            output += "\n"

        if 'language' in results:
            lang = results['language']
            output += f"LANGUAGE: {lang['language'].upper()} (confidence: {lang['confidence']})\n\n"

        if 'stats' in results:
            st = results['stats']
            output += f"TEXT STATISTICS:\n"
            output += f"  Characters: {st['characters']} (no spaces: {st['characters_no_spaces']})\n"
            output += f"  Words: {st['words']} (unique: {st['unique_words']})\n"
            output += f"  Sentences: {st['sentences']}\n"
            output += f"  Avg Word Length: {st['avg_word_length']} chars\n"
            output += f"  Avg Sentence Length: {st['avg_sentence_length']} words\n"

        return output

    except Exception as e:
        return f"NLP analysis error: {str(e)}"
