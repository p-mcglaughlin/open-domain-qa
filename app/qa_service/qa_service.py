from huggingface_qa import Default_Hugging_Face_QA, OpenVINO_QA
from triton_inference_qa import Triton_Inference_QA_Client
from transformers import AutoTokenizer
import logging, time

class QA_Service:
    def __init__(self, qa_model, is_async=False):
        self.qa_model = qa_model
        self.is_async = is_async # only used for triton inference
        # set logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        console_handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')
        console_handler.setFormatter(formatter) 
        self.logger.addHandler(console_handler)

    @classmethod
    def make_default_service(cls) -> 'QA_Service':
        '''
        returns Hugging Face model: distilbert-base-cased-distilled-squad
        '''
        # change model name to whatever you want to use
        qa_model_name = "distilbert/distilbert-base-cased-distilled-squad"
        qa_model = Default_Hugging_Face_QA(qa_model_name)
        return QA_Service(qa_model)
    
    @classmethod
    def make_quantized_service(cls) -> 'QA_Service':
        '''
        returns INT8 quantized model running in OpenVino
        '''
        # assumes model is quantized from something available on Hugging Face 
        # name of original Hugging Face model, required to use correct tokenizer
        qa_model_name = 'distilbert/distilbert-base-cased-distilled-squad'
        int8_model_path = './models/distilbert-base-cased-distilled-squad_INT8_PTQ'
        qa_model = OpenVINO_QA(qa_model_name, int8_model_path)
        return QA_Service(qa_model)
    
    @classmethod
    def make_triton_service(cls, host: str, port: int) -> 'QA_Service':
        '''
        returns client from Nvidia Triton Inference Server running on {host}:{port}
        '''
        # regardless of backed: PyTorch, OpenVino, TensorRT; we need tokenizer from Hugging Face
        # name of Hugging Face model to use for tokenizer
        qa_model_name = 'distilbert/distilbert-base-cased-distilled-squad'
        tokenizer = AutoTokenizer.from_pretrained(qa_model_name)
        qa_model = Triton_Inference_QA_Client(host, port, tokenizer)
        return QA_Service(qa_model, is_async=True)
    
    async def get_answers(self, question, contexts):
        '''
        returns one answer to question for each context in contexts
        '''
        k = len(contexts)
        questions = [question]*k
        qa_contexts = [context['text'] for context in contexts]
        s = time.time()
        if self.is_async:
            results = await self.qa_model.answer(questions = questions, contexts = qa_contexts)
        else:
            results = self.qa_model.answer(questions = questions, contexts = qa_contexts)
        t = 1000*(time.time()-s)
        self.logger.info(f'qa compute time: {t}')
        return results