from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from nearest_neighbors_service.ann_service import SearchType
from qa_manager import QA_Manager

vdb_host = os.getenv("VDB_HOST", "localhost")
vdb_port = os.getenv('VDB_PORT', '6333')
ft_host = os.getenv("FT_HOST", "localhost")
ft_port = os.getenv("FT_PORT", 9200)
qa_type = os.getenv('QA_TYPE', 'openvino')
inference_host = os.getenv('INFERENCE_HOST', 'localhost')
inference_port = os.getenv('INFERENCE_PORT', 9000)
# for running Node.js server on same machine
allow_CORS_origin = os.getenv('ALLOW_CORS_ORIGIN', 'http://localhost:3000')

manager = QA_Manager.make_default_manager(
                        vdb_host, 
                        vdb_port, 
                        ft_host,
                        ft_port,
                        qa_type,
                        inference_host, 
                        inference_port
                    )

app = FastAPI()

if allow_CORS_origin:
    origins = [allow_CORS_origin]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

@app.get("/")
async def root():
    return {"message": "loaded successfully"}

@app.get('/ask')
async def get_answer(question: str, search_type: str) -> list[dict]:
    '''
    returns possible answers for question with extractive qa, 
    finds relevant documents based on search_type: 
        VEC = vector only
        FT = full-text only
        VEC_FT = hybrid search with reranking
    '''
    search_type = SearchType.from_string(search_type)
    return await manager.answer(question, search_type)
