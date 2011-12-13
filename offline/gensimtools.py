from gensim import corpora, models, similarities
from nltk import word_tokenize
import os
import pickle

def tokenize(text):
    return word_tokenize(text.lower())

def ensure_directory(directory):
    if not os.path.exists(directory):
        os.mkdir(directory)
            
class GensimIndexer:
    
    def __init__(self, directory):
        ensure_directory(directory)
        self.directory = directory
    
    def index(self, documents):
        
        texts = map(tokenize, documents)
        
        # ID to document name
        id2doc = dict([(i, document) for i, document in enumerate(documents)])
        pickle.dump(id2doc, open('%s/id2doc' % self.directory, 'w'))
        
        # Dictionary
        dictionary = corpora.Dictionary(texts)
        dictionary.save('%s/gensim.dict' % self.directory)
        
        # Corpus
        corpus = [dictionary.doc2bow(text) for text in texts]
        corpora.MmCorpus.serialize('%s/gensim.mm' % self.directory, corpus)
        
        # TFIDF Model
        tfidf = models.TfidfModel(corpus)
        tfidf.save('%s/gensim.tfidf' % self.directory)
        
        # Index
        #index = similarities.MatrixSimilarity(tfidf[corpus])
        #index.save('%s/gensim.index' % self.directory)

class GensimSearcher:
    
    def __init__(self, directory):
        ensure_directory(directory)
        self.directory = directory
        
        self.dictionary = corpora.Dictionary.load('%s/gensim.dict' % self.directory)
        corpus = corpora.MmCorpus('%s/gensim.mm' % self.directory)
        self.id2doc = pickle.load(open('%s/id2doc' % self.directory, 'r'))
        
        self.tfidf = models.TfidfModel.load('%s/gensim.tfidf' % self.directory)
        #self.index =  similarities.MatrixSimilarity.load('%s/gensim.index' % self.directory)
        
        self.index = similarities.Similarity('%s/gensim.index' % self.directory, corpus, num_features=len(self.dictionary))
    
    def search(self, text):
        vec_bow = self.dictionary.doc2bow(tokenize(text))
        vec_tfidf = self.tfidf[vec_bow]
        
        sims = self.index[vec_tfidf]
        return [(self.id2doc[id], cosine) for id, cosine in sorted(enumerate(sims), key=lambda item: -item[1]) if cosine > 0]
        