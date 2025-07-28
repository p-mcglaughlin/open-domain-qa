from sentence_transformers import CrossEncoder
from transformers import AutoTokenizer
from optimum.intel import OVModelForSequenceClassification
from abc import ABC

class Reranker(ABC):
    def predict(self, query: str, contexts: list[dict]) -> list[dict]:
        '''
        add similarity score between query and context for each context in contexts
        '''
        ...
    
    def rerank(self, query: str, contexts: list[dict]) -> list[dict]:
        '''
        return contexts sorted in decreasing order of similarity to query
        '''
        scores = self.predict(query, contexts)
        for context, score in zip(contexts, scores):
            context['score'] = score
        contexts.sort(key = lambda x: x['score'], reverse = True)
        return contexts
    
class HugginFace_Reranker(Reranker):
    def __init__(self, model_name):
        '''
        wrapper for SentenceTransformers CrossEncoder models
        '''
        self.model = CrossEncoder(model_name)
    
    def predict(self, query, contexts):
        scores = self.model.predict(
                [(query, context['text']) for context in contexts]
            )
        return scores
    
    def rerank(self, query, contexts):
        return super().rerank(query, contexts)
    
class OpenVINO_Reranker(Reranker):
    def __init__(self, model_name, model_path):
        '''
        returns INT8 quantized verison of model_name running with OpenVino backend
            model_name = original SentenceTransformer CrossEncoder model name
            model_path = path to OpenVino model
        '''
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = OVModelForSequenceClassification.from_pretrained(model_path)
    
    def predict(self, query, contexts):
        k = len(contexts)
        inputs = self.tokenizer(
                    [query]*k, 
                    [context['text'] for context in contexts], 
                    padding='longest',
                    truncation=True,
                    return_tensors='pt'
                )
        logits = self.model(**inputs).logits
        # the model cross-encoder/ms-marco-MiniLM-L6-v2 returns similarity scores between [-10, 10]
        # this normalizes scores to be between [0-1]
        scores = [round((float(score)+10)/20, 4) for score in logits]
        return scores
    
    def rerank(self, query, contexts):
        return super().rerank(query, contexts)