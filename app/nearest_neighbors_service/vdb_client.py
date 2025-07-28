from abc import ABC, abstractmethod
from enum import Enum
import numpy as np
import json
from tqdm import tqdm

class Distance(Enum):
    DOTPRODUCT = 0
    COSINE = 1
    L2 = 2

class DB_Entry:
    '''
    struct for database entries
    '''
    def __init__(self, key: str, embedding: np.array, fields: dict=None):
        self.key = key
        self.embedding = embedding
        self.fields = fields

    @classmethod
    def from_json(cls, json_obj: dict, quantization: np.dtype=np.float32):
        fields = {k: str(v) for k, v in json_obj.items() if k not in ['embedding']}
        key = f"{json_obj['id']}-{json_obj['chunk']}"
        json_obj["embedding"] = np.array(json_obj["embedding"]).astype(quantization)
        return DB_Entry(key=key, embedding=json_obj['embedding'], fields=fields)

class VDB_Client(ABC):
    '''
    abstract method serves as wrapper for different database clients
    '''
    def __init__(self, host: str, port: str, *args):
        self.host = host
        self.port = port
        self.client = None
        self._connect(host, port, *args)
    
    @abstractmethod
    def _connect(self, host: str, port: str, *args) -> bool:
        ...

    @abstractmethod
    async def create_index(self, name: str, dim: int, distance: Distance, quantization: np.dtype, fields: list[str]=None) -> bool:
        ...

    @abstractmethod
    async def delete_index(self, name: str) -> bool:
        ...
    
    @abstractmethod
    def configure_query(self, return_fields: list[str]=None) -> None:
        ...

    @abstractmethod
    async def insert(self, entry: DB_Entry) -> bool:
        ...

    async def insert_group(self, entries: list[DB_Entry]) -> bool:
        results = []
        for entry in entries:
            results.append(self.insert(entry))
        return all(results)
    
    @abstractmethod
    async def query(self, index: str, vector: np.array, k: int) -> dict:
        ...

    async def query_group(self, index: str, vectors: list[np.array], k: int) -> dict:
        docs = []
        for vector in vectors:
            docs.append(self.query(index, vector, k))
        return docs