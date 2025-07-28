from vdb_client import VDB_Client, Distance, DB_Entry
import numpy as np
import redis

class REDIS_VSET_Client:
    def __init__(self, host: str='localhost', port: str='6379', *args):
        self.host = host
        self.port = port
        try:
            self.client = redis.asyncio.Redis(host=self.host, port=self.port, decode_responses=True)
        except Exception as e:
            print(e)

    def _connect(self, host: str, port: str, *args) -> bool:
        try:
            self.client = redis.Redis(host=self.host, port=self.port, decode_responses=True)
        except Exception as e:
            print(e)
            return False
        return True
    
    def create_index(self, name, dim, distance, quantization, fields = None):
        self.idx_name = name
        return True
    
    async def delete_index(self, name):
        ...
    
    def configure_query(self, return_fields = None):
        self.return_fields = return_fields
        return True
    
    async def insert(self, entry):
        res = await self.client.vset().vadd(
            self.idx_name,
            entry.embedding.tobytes(),
            entry.fields['group'],
        )
        return res
    
    async def insert_group(self, entries):
        pipeline = self.client.pipeline()
        for entry in entries:
            pipeline.vset().vadd(
                self.idx_name,
                entry.embedding.tobytes(),
                str(entry.key),
            )
            pipeline.vset().vsetattr(self.idx_name, entry.key, entry.fields)
        return await pipeline.execute()

    async def query(self, index, vector, k):
        docs = await self.client.vset().vsim(
            index,
            vector.tobytes(),
            with_scores=True,
            count = k,
        )
        pipeline = self.client.pipeline()
        for id in docs:
            pipeline.vset().vgetattr(index, id)
        results = await pipeline.execute()
        for res, id in zip(results, docs):
            res['score'] = docs[id]
            res['id'] = int(res['id'])
        return results
    
    def query_group(self, index, vectors, k):
        ...