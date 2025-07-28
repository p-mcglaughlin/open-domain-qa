from vdb_client import VDB_Client, Distance, DB_Entry
import pgvector.psycopg
import pgvector, psycopg
import numpy as np
import json

class PG_Client:
    Quantization_Mapping = {np.float32: 'vector', np.float16: 'halfvec'}
    Distance_Mapping = {Distance.COSINE: 'cosine', Distance.DOTPRODUCT: 'ip'}
    Search_Mapping = {Distance.COSINE: '=', Distance.DOTPRODUCT: '#'}

    def __init__(self, host, port, username, password):
        self.distance = Distance.COSINE
        uri = f"postgresql://{username}:{password}@{host}:{port}"
        try:
            self.conn = psycopg.connect(uri)
        except Exception as e:
            print(e)
        self.conn.execute('CREATE EXTENSION IF NOT EXISTS vector')
        pgvector.psycopg.register_vector(self.conn)

    def create_index(self, name, dim, distance, quantization, fields = None):
        self.distance = distance
        vec_type = PG_Client.Quantization_Mapping[quantization]
        dist_type = PG_Client.Distance_Mapping[distance]
        make_table = f"CREATE TABLE items (id bigint PRIMARY KEY, embedding {vec_type}({dim}), fields JSON)"
        make_index = f"CREATE INDEX ON items USING hnsw (embedding {vec_type}_{dist_type}_ops)"
        try:
            self.conn.execute(make_table)
            self.conn.execute(make_index)
        except Exception as e:
            print(e)
        return True
    
    def delete_index(self, name):
        pass
    
    def insert(self, entry):
        k = entry.key
        e = entry.embedding
        f = json.dumps(entry.fields)
        out = self.conn.execute('INSERT INTO items (id, embedding, fields) VALUES (%s, %s, %s)', (k, e, f))  
        return out

    def insert_group(self, entries):
        for entry in entries:
            self.insert(entry)
        return True
    
    def configure_query(self, return_fields = None):
        dist = f"embedding <{PG_Client.Search_Mapping[self.distance]}> %s"
        to_return = f"{dist} as score"
        to_return += ", fields as fields_json"
        self._q = f"SELECT {to_return} FROM items ORDER BY {dist} LIMIT %s"
    
    def query(self, index, vector, k):
        if not self._q:
            self.configure_query()
        #s = self.conn.execute('SELECT * FROM items ORDER BY embedding <-> %s LIMIT %s', (vector,k,)).fetchall()
        results = self.conn.execute(self._q, (vector,vector,k,)).fetchall()
        docs = []
        for res in results:
            doc = res[1]
            doc["score"] = res[0]
            docs.append(doc)
        return docs
    
    def query_group(self, index, vectors, k):
        pass

if __name__ == "__main__":
    client = PG_Client('localhost', '5432', 'Pete', 'tonko')
    client.create_index("a", 3, Distance.COSINE, np.float32)

    v = [[1, 0, 0], [0, 1, 0], [0, 0, 1], [1, 0.5, 0], [0, 1, 0.5]]
    es = [np.array(l).astype(np.float32) for l in v]
    strs = ['Fauna is cool!', 'Tonka is the best!', 'What will return?', 'Charlie is a goof', 'This is just a test sentence.']
    fs = [{"text":s} for s in strs] 
    entries = [DB_Entry(i, es[i], fs[i]) for i in range(len(es))]
    client.insert_group(entries)
    client.configure_query()
    vector = np.array([1,0,1])
    s = client.query("a", vector, 2)
    print(s)
