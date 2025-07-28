from opensearchpy import AsyncOpenSearch
from vdb_client import VDB_Client, DB_Entry
import json
import time

class FakeEmbedding:
    def __init__(self):
        pass

    def encode(self, s):
        return s

class OPENSEARCH_Client(VDB_Client):
    def __init__(self, host, port, *args):
        self.host = host
        self.port = int(port)
        self.client = AsyncOpenSearch(
            hosts = [{'host': host, 'port': port}],
            http_compress = True,
            use_ssl = False,
            verify_certs = False,
            ssl_assert_hostname = False,
            ssl_show_warn =False
        )
    
    def _connect(self, host, port, *args):
        pass
    
    async def create_index(self, name, dim, distance, quantization, fields = None):
        self.index = name
        index_body = {
            'settings': {
                'index': { 'number_of_shards': 1, 'number_of_replicas': 0}   
                },
            'mappings': {
                'properties': {
                    'content': {
                        'type': 'text',
                        'analyzer': 'english'
                    }
                }    
            }
        }
        return await self.client.indices.create(index=name, body=index_body)
    
    async def delete_index(self, name):
        return await super().delete_index(name)
    
    async def configure_query(self, return_fields = None):
        pass

    async def insert(self, entry):
        response = await self.client.index(
            index = self.index,
            body = entry.fields,
            id = str(entry.key),
            refresh = True
        )
        return response
    
    async def insert_group(self, entries):
        jsons = []
        for entry in entries:
            insert_command = {"index": {"_index": self.index, "_id": entry.key}}
            jsons.append(json.dumps(insert_command))
            jsons.append(json.dumps(entry.fields))
        cmd = '\n'.join(jsons)
        response = await self.client.bulk(body=cmd)
        return response
    
    async def query(self, index, vector, k):
        s = time.time()
        query = {
            "size": k,
            "query": {
                "match": {
                    "text": {
                        "query": vector
                    } 
                }    
            }
        }
        response = await self.client.search(body=query, index=index)
        response = response['hits']['hits']
        docs = []
        for res in response:
            doc = res['_source']
            doc['score'] = res['_score']
            docs.append(doc)
        return docs