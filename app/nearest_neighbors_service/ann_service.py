from sentence_transformers import SentenceTransformer
from qdrantdb_client import QDRANT_Client
from opensearch_client import OPENSEARCH_Client
from reranking_models import OpenVINO_Reranker
from enum import Enum
import time, logging, asyncio

class SearchType(Enum):
    VECTOR_AND_FULLTEXT = 0
    VECTOR_ONLY = 1
    FULLTEXT_ONLY = 2

    @classmethod
    def from_string(cls, s):
        _type = SearchType.VECTOR_AND_FULLTEXT
        if s == 'VEC':
            _type = SearchType.VECTOR_ONLY
        elif s == 'FT':
            _type = SearchType.FULLTEXT_ONLY
        return _type

class NearestNeighborService:
    def __init__(self, 
                 embedding_model, 
                 vector_db_client,
                 fulltext_client,
                 reranking_model=None, 
                 search_idx='wiki', 
                ):
        self.embedding_model = embedding_model
        self.vector_db_client = vector_db_client
        self.fulltext_client = fulltext_client
        self.reranking_model = reranking_model
        self.search_idx = search_idx
        # set logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        console_handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')
        console_handler.setFormatter(formatter) 
        self.logger.addHandler(console_handler)
    
    @classmethod
    def make_default_service(cls, 
            vector_db_host, 
            vector_db_port,
            fulltext_host,
            fulltext_port, 
        ):
        '''
        returns hybrid search (embeddings and BM25) service with reranking, runs on CPU
        '''
        # embedding model
        embedding_name = 'Snowflake/snowflake-arctic-embed-s'
        embedding_model = SentenceTransformer(embedding_name)
        # vector db
        vdb_client = QDRANT_Client(vector_db_host, vector_db_port)
        # full-text search
        ft_client = OPENSEARCH_Client(fulltext_host, fulltext_port)
        # reranker, assumes model is stored in models folder
        reranker_name = 'cross-encoder/ms-marco-MiniLM-L6-v2'
        reranker_path = './models/ms-marco-MiniLM-L6-v2_INT8_PTQ'
        reranker = OpenVINO_Reranker(reranker_name, reranker_path)
        return NearestNeighborService(
                    embedding_model, 
                    vdb_client, 
                    ft_client,
                    reranking_model = reranker
                )
    
    async def query(
                self, 
                question: str, 
                k: int, 
                search_type: SearchType=SearchType.VECTOR_AND_FULLTEXT,
                rerank: bool=True
                ) -> list[dict]:
        '''
        returns top k relevant documents for question using search_type and rerank
        '''
        
        clients, embeddings = [], []
        if search_type in [SearchType.VECTOR_AND_FULLTEXT, SearchType.VECTOR_ONLY]:
            # search vector embeddings
            s = time.time()
            embedding = self.embedding_model.encode(question, prompt_name='query')
            # for generic SentenceTransformer models use the version below instead
            # embedding = self.embedding_model.encode(question)
            embed_t = time.time()-s
            self.logger.info(f'emedding time {embed_t}')
            clients.append(self.vector_db_client)
            embeddings.append(embedding)

        if search_type in [SearchType.VECTOR_AND_FULLTEXT, SearchType.FULLTEXT_ONLY]:
            # full-text search
            clients.append(self.fulltext_client)
            embeddings.append(question)
        
        contexts = []
        s = time.time()
        async with asyncio.TaskGroup() as tg:
            tasks = [tg.create_task(
                        client.query(
                            self.search_idx, 
                            embed, 
                            k
                        )
                    ) for client, embed in zip(clients, embeddings)] 
        for task in tasks:
            contexts.extend(task.result())
        search_t = time.time()-s
        total_contexts = len(contexts)
        self.logger.info(f'search time for {total_contexts} contexts: {search_t}')

        rerank_t = 0
        if rerank:
            s = time.time()
            contexts = self.reranking_model.rerank(question, contexts)
            rerank_t = time.time()-s
            self.logger.info(f'reranking time for {total_contexts}: {rerank_t}')

        return contexts[:k]
    
