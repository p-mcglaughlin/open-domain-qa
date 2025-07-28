from vdb_client import VDB_Client, Distance, DB_Entry
from qdrant_client import AsyncQdrantClient, models
import numpy as np
import time

class QDRANT_Client(VDB_Client):
    distance_mapping = {Distance.COSINE: models.Distance.COSINE, Distance.DOTPRODUCT: models.Distance.DOT}
    quatization_mapping = {np.float32: models.Datatype.FLOAT32, np.float16: models.Datatype.FLOAT16}

    def __init__(self, host: str, port: str, *args):
        super().__init__(host, port, *args)
    
    def _connect(self, host: str, port: str, *args) -> bool:
        try:
            url = f"http://{host}:{port}"
            print(url)
            self.client = AsyncQdrantClient(url=url)
        except Exception as e:
            print(e)
            return False
        return True
    
    async def create_index(self, name, dim, distance, quantization, fields = None, kw_args=None) -> bool:
        self.index = name
        DIST = QDRANT_Client.distance_mapping[distance]
        QUANTIZATION = QDRANT_Client.quatization_mapping[quantization]
        hnsw_config = None
        if kw_args:
            hnsw_config = models.HnswConfigDiff(m=kw_args['m'], ef_construct=kw_args['ef_construct'])
        try:
            await self.client.create_collection(
                collection_name=name,
                vectors_config=models.VectorParams(
                    size=dim,
                    distance=DIST,
                    datatype=QUANTIZATION,
                    hnsw_config=hnsw_config
                ),
            )
        except Exception as e:
            print(e)
        return True

    async def delete_index(self, name) -> None:
        try:
            await self.client.delete_collection(collection_name=name)
        except Exception as e:
            print(e)
        return True

    def configure_query(self, return_fields = None):
        # not currently implemented
        return True
    
    async def insert_group(self, entries):
        points = [models.PointStruct(
                    id=int(e.key),
                    vector=e.embedding.tolist(),
                    payload=e.fields
                ) for e in entries]
        try:
            await self.client.upsert(collection_name=self.index, points=points)
        except Exception as e:
            print(e)
        return True

    async def insert(self, entry):
        return await self.insert_group([entry])
    
    async def query(self, index, vector, k, ef=200):
        #params = models.SearchParams(hnsw_ef=ef)
        s = time.time()
        results = await self.client.query_points(
            collection_name=index,
            query=vector.tolist(),
            limit=k,
        )
        t = time.time()-s
        t = 1000*round(t,4)
        print(f'vector db search: {t}')
        docs = []
        for point in results.points:
            doc = point.payload
            doc["score"] = point.score  
            docs.append(doc)
        return docs
