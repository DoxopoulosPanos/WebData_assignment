import requests


def search(domain, query, size=20):
    url = 'http://%s/freebase/label/_search' % domain
    response = requests.get(url, params={'q': query, 'size': size})
    id_labels = {}
    if response:
        response = response.json()
        for hit in response.get('hits', {}).get('hits', []):
            freebase_label = hit.get('_source', {}).get('label')
            freebase_id = hit.get('_source', {}).get('resource')
            id_labels.setdefault(freebase_id, set()).add(freebase_label)
    return id_labels


def get_best_candidates(domain, query, results_No=10):
    """
    Finds the best candidates according to the freebase _score
    :param domain:
    :param query:
    :param size:
    :return:
    """
    url = 'http://%s/freebase/label/_search' % domain
    # fetch 100 results from freebase
    response = requests.get(url, params={'q': query, 'size': 100})
    best_id_labels = {}
    id_labels = []
    if response:
        response = response.json()
        for hit in response.get('hits', {}).get('hits', []):
            freebase_label = hit.get('_source', {}).get('label')
            freebase_id = hit.get('_source', {}).get('resource')
            score = hit.get('_score')
            id_labels.append([freebase_id, score, freebase_label])

        # find the top 10 according to the score
        id_labels = sorted(id_labels, key=lambda x: x[1], reverse=True)       # sort entries in list according to 2nd value (score)
        for i in range(results_No):
            try:
                best_id_labels.setdefault(id_labels[i][0], set()).add(id_labels[i][2])
            except:
                # candidates found less than results_No
                break

    return best_id_labels


if __name__ == '__main__':
    import sys
    try:
        _, DOMAIN, QUERY = sys.argv
    except Exception as e:
        print('Usage: python elasticsearch.py DOMAIN QUERY')
        sys.exit(0)

    for entity, labels in search(DOMAIN, QUERY).items():
        print(entity, labels)
