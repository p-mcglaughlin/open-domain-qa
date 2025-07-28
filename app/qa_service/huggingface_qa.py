from transformers import AutoTokenizer, pipeline
from optimum.intel import OVModelForQuestionAnswering

class Default_Hugging_Face_QA:
    def __init__(self, model_name):
        '''
        wrapper for Hugging Face question answering pipeline using: model_name
        '''
        self.model = pipeline('question-answering', model = model_name)
    
    def answer(self, questions, contexts):
        return self.model(question=questions, context=contexts)

class OpenVINO_QA:
    def __init__(self, model_name, model_path):
        '''
        wrapper for Hugging Face question answering pipeline using INT8 quantized version of: model_name
            model_name: name of original Hugging Face model, required for tokenizer
            model_path: path to OpenVino model
        '''
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = OVModelForQuestionAnswering.from_pretrained(model_path)
        self.model = pipeline("question-answering", model=model, tokenizer=tokenizer)
    
    def answer(self, questions, contexts):
        return self.model(question=questions, context=contexts)
