from nearest_neighbors_service.ann_service import NearestNeighborService, SearchType
from qa_service.qa_service import QA_Service
import logging

class QA_Manager:
    def __init__(self, nearest_neighbor_service, qa_service, k: int=5):
        self.nearest_neighbor_service = nearest_neighbor_service
        self.qa_service = qa_service
        self.k = k
        # these files store titles and urls for popular pages
        self.hrefs = self.load_page_info('/data/popular_hrefs.txt')
        self.titles = self.load_page_info('/data/popular_titles.txt')
    
    def load_page_info(self, file):
        '''
        for loading titles and urls of popular wiki pages
        '''
        with open(file, 'r') as f:
            return f.read().split('\n')
    
    @classmethod
    def make_default_manager(cls, 
                     vector_db_host = 'localhost',
                     vector_db_port = '6333', 
                     fulltext_host = 'localhost',
                     fulltext_port = '9200',
                     qa_type = 'openvino',
                     inference_host = 'localhost', 
                     inference_port = '9000',
                    ):
        '''
        creates the following:
        - hybrid search for relevant documents
            * embedding model = Snowflake/snowflake-arctic-embed-s running in PyTorch
            * HNSW index in Qdrant
            * BM25 fulltext search in OpenSearch
            * reranking with INT8 quantized version of cross-encoder/ms-marco-MiniLM-L6-v2
                running in OpenVino
        - extractive question answering with distilbert/distilbert-base-cased-distilled-squad
            * if qa_type = trition, then provide the host and port for Nvidia Triton Inference Server
              o.w. uses INT8 quantized version running in OpenVino
        '''
        ann_service = NearestNeighborService.make_default_service(
            vector_db_host, 
            vector_db_port, 
            fulltext_host, 
            fulltext_port
        )
        # selecting triton will run question answering compute on triton inference server
        # this works with both GPU enabled and CPU only hosts, otherwise default to compute
        # on same CPU as backend 
        # in both cases, assumes model is stored in models folder
        if qa_type == 'triton':
            qa_service = QA_Service.make_triton_service(inference_host, inference_port)
        else:
            qa_service = QA_Service.make_quantized_service()
        return QA_Manager(ann_service, qa_service)
        
    async def answer(self, question: str, search_type: SearchType):
        '''
        returns k possible answers to question
        '''
        contexts = await self.nearest_neighbor_service.query(question, self.k, search_type)
        answers = await self.qa_service.get_answers(question, contexts)
        ans = [{'score' : float(context['score']),
                'ans' : answers[i]['answer'],
                'HNSW_score' : float(context['score']),
                'QA_score' : answers[i]['score'],
                'href': self.hrefs[int(context['id'])], 
                'id': context['id'],
                'title': self.titles[int(context['id'])],
                'text': context['text']} for i, context in enumerate(contexts)]
        return ans
