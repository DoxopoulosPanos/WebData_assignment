"""
This module is used in order to query the knowledge base
"""

import requests
import json
import time


def sparql(domain, query):
    """
    Queries the knowledge base
    :param domain:
    :param query:
    :return:
    """
    url = 'http://%s/sparql' % domain
    response = requests.post(url, data={'print': True, 'query': query})
    if response:
        retries = 3

        while retries > 0:
            retries = retries - 1
            try:
                response = response.json()
                # print(json.dumps(response, indent=2))
                break
            except Exception as exception:
                if retries > 0:
                    # in case of connection error wait 2 second and retry
                    time.sleep(2)
                    continue
                else:
                    # if last retry fails then print the Error
                    print(response)
                    raise exception

    return response


if __name__ == '__main__':
    import sys
    try:
        _, DOMAIN, QUERY = sys.argv
    except Exception as e:
        print('Usage: python sparql.py DOMAIN QUERY')
        sys.exit(0)

    sparql(DOMAIN, QUERY)
