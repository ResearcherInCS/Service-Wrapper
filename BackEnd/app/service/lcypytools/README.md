# My often-used python library

## in the *common* package

- load_csv(path): return a two dimensional array from a csv file.

- load_lines(file): load lines from a txt file, and replace all "\n"s to "".

- prepare_clean_dir(directory): create a folder according to directory if it is not exist, and clean all files in the folder.

- prepare_dir(directory): create a folder according to directory if not exist.


- get_filename_and_postfix_from_path(path): from a file path, get the filename and postfix of the file.

- current_datetime(): get current time string

- log (class): write log to run.log

```python
from common import log
l = log()
l.write("write a line of log")
```

- save_json(path, data): save a json object to path

- load_json(path, encoding="utf-8"): load a json object from path

- clean_folder(folder): remove all files in a folder

- save_pickle(path, obj): save a object to path

- load_pickle(path): load a object from path

- get_hostname_from_url(url): get hostname from a url

- is_path_exists(path): detect path exists or not

## in the *mongo* package

- about init class

```python
from mongo import Mongo
mdb = Mongo(db="test", server='localhost', port=27017)
```

- mdb.insert_with_seqid(col, doc): insert document 'doc' in collection 'col' with auto increased _id from 1.

- mdb.remove_all_documents(col): remove all documents in collection 'col'.

- mdb.find_all(col): find all documents in collection 'col'.

- mdb.find_one(col, query): find one (first) document in collection 'col' within query.

- mdb.save(col, doc): save document 'doc' into collection 'col', if _id exists then update it.

- mdb.find(col, query): find all documents in collection 'col' within query.

- mdb.find_snapshot(col, query, timeout=False): find all documents in collection 'col' within query as snapshot.

- mdb.find_sort(col, query, sortkey, sortorder): find all documents in collection 'col' within query sorted by sortkey

- mdb.count(col, query): count number of documents with query

- mdb.aggregate(col, pipeline): aggregate query

- mdb.close(): close mongodb link