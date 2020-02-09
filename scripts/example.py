import elasticsearch as els
import entity

if __name__ == '__main__':
    import sys

    try:
        _, ELS_DOMAIN, ELS_QUERY = sys.argv
    except Exception as e:
        print('Usage: python elasticsearch.py DOMAIN QUERY')
        sys.exit(0)

    total_entities = []
    for freebase_id, labels in els.search(ELS_DOMAIN, ELS_QUERY).items():
        my_entity = entity.Entity(ELS_QUERY)
        my_entity.freebase_id = freebase_id
        my_entity.freebase_label = labels
        print(my_entity)
        total_entities.append(my_entity)

