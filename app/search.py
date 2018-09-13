from flask import current_app

def add_to_index(index, model):
    if not current_app.elasticsearch:
        return
    payload = {}
    for field in model.__searchable__:
        payload[field] = getattr(model, field)
    current_app.elasticsearch.index(index=index, doc_type=index,
        id=model.id, # Use SQLAlchemy model's id for Elasticsearch document id
        body=payload)

def remove_from_index(index, model):
    if not current_app.elasticsearch:
        return
    current_app.elasticsearch.delete(index=index, doc_type=index, id=model.id)

def query_index(index, query, page, per_page):
    if not current_app.elasticsearch:
        return [], 0
    search = current_app.elasticsearch.search(
        index=index, doc_type=index, body={
            'query': { 'multi_match': {'query': query, 'fields': ['*']} },
            'from': (page-1) * per_page,
            'size': per_page
        })
    ids = [int(hit['_id']) for hit in search['hits']['hits']] # List comprehension (python)
    return ids, search['hits']['total']

##### Python console example #####
# >>> es.search(index='my_index', doc_type='my_index',
# ... body={'query': {'match': {'text': 'second'}}})
# {
#     'took': 1,
#     'timed_out': False,
#     '_shards': {'total': 5, 'successful': 5, 'skipped': 0, 'failed': 0},
#     'hits': {
#         'total': 1,
#         'max_score': 0.25316024,
#         'hits': [
#             {
#                 '_index': 'my_index',
#                 '_type': 'my_index',
#                 '_id': '2',
#                 '_score': 0.25316024,
#                 '_source': {'text': 'a second test'}
#             }
#         ]
#     }
# }
