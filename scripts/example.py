import elasticsearch as els
import entity

if __name__ == '__main__':
    import sys

    try:
        _, ELS_DOMAIN, ELS_QUERY = sys.argv
    except Exception as e:
        print('Usage: python elasticsearch.py DOMAIN QUERY')
        sys.exit(0)

    my_entity = entity.Entity(ELS_QUERY)

    for freebase_id, labels in els.search(ELS_DOMAIN, ELS_QUERY).items():
        my_entity.set_freebase_values(freebase_id, labels)

    print(my_entity)
