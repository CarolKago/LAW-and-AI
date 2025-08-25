import nltk
from nltk.tokenize import sent_tokenize
from nltk.corpus import stopwords
from heapq import nlargest

nltk.download('punkt')
nltk.download('stopwords')

def summarize_text(text, num_sentences=3):
    sentences = sent_tokenize(text)
    stop_words = set(stopwords.words('english'))
    
    word_frequencies = {}
    for sentence in sentences:
        for word in nltk.word_tokenize(sentence.lower()):
            if word not in stop_words:
                word_frequencies[word] = word_frequencies.get(word, 0) + 1
    
    sentence_scores = {}
    for sentence in sentences:
        for word in nltk.word_tokenize(sentence.lower()):
            if word in word_frequencies:
                sentence_scores[sentence] = sentence_scores.get(sentence, 0) + word_frequencies[word]
    
    summary_sentences = nlargest(num_sentences, sentence_scores, key=sentence_scores.get)
    return ' '.join(summary_sentences)

# Example usage
legal_text = "This is a sample legal document. It contains clauses about AI usage. Lawyers must navigate ethics."
print(summarize_text(legal_text))
