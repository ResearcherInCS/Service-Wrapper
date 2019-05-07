import pymongo as pm


class Mongo:
    SEQS = "sys_seqs"

    def __init__(self, db="test", server='localhost', port=27017):
        self.client = pm.MongoClient(server, port)
        self.db = self.client[db]

    def __check_seq(self, col):
        if self.db[self.SEQS].find_one({'col': col}) is None:
            self.db[self.SEQS].insert_one({'col': col, 'id': 0})
            self.db[self.SEQS].create_index([('col', pm.TEXT)], name='i_col')

    def insert_with_seqid(self, col, doc):
        self.__check_seq(col)

        doc['_id'] = self.db[self.SEQS].find_and_modify(
            query={'col': col},
            update={'$inc': {'id': 1}},
            fields={'id': 1, '_id': 0},
            new=True
        ).get('id')

        self.db[col].insert(doc)

    def remove_all_documents(self, col):
        self.db[col].remove()

    def find_all(self, col):
        return self.db[col].find()

    def find_one(self, col, query):
        return self.db[col].find_one(query)

    def save(self, col, doc):
        self.db[col].save(doc)

    def find(self, col, query):
        return self.db[col].find(query)

    def find_snapshot(self, col, query, timeout=False):
        return self.db[col].find(query, snapshot=True, timeout=timeout)

    def find_sort(self, col, query, sortkey, sortorder):
        return self.db[col].find(query).sort(sortkey, sortorder)

    def count(self, col, query):
        return self.db[col].count(query)

    def aggregate(self, col, pipeline):
        return self.db[col].aggregate(pipeline=pipeline)

    def close(self):
        self.client.close()


if __name__ == "__main__":
    mongo = Mongo()
    mongo.insert_with_seqid("test", {"test": "test"})
