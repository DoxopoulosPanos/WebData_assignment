import sys
import logging
import json

import elasticsearch as els
import sparql
import preprocessing
import entity

#  define logger as global variable
logger = logging.getLogger(__name__)


########################################################
#                      logger functions                #
########################################################
def map_logging_level(level):
    """
    This function maps the input level with the logging level
    :param level: e.g. "debug", "info"
    :return: logging level
    """
    log_map = {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warning": logging.WARNING,
        "error": logging.ERROR
    }

    return log_map[level]


def set_logger(stream_level="info", file_level="error", log_filename="file.log"):
    """
    This function is used in order to set the level of the global logger
    :param stream_level: logging level for printing(e.g. logging.DEBUG)
    :param file_level: logging level for writing in log file (e.g. logging.DEBUG)
    :param log_filename: the path to the file that logs will be stored
    :return:
    """
    global logger

    # find level
    stream_log_level = map_logging_level(stream_level)
    file_log_level = map_logging_level(file_level)
    # create console handler with a higher log level
    stream_handler = logging.StreamHandler()
    file_handler = logging.FileHandler(log_filename)
    # set logger level
    logger.setLevel(logging.DEBUG)
    # set handler level
    stream_handler.setLevel(stream_log_level)
    file_handler.setLevel(file_log_level)
    # create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    stream_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    # add the handlers to the logger
    logger.addHandler(stream_handler)
    logger.addHandler(file_handler)
    logger.propagate = False


########################################################
#              elastic search functions                #
########################################################
def find_candidates(ES_DOMAIN, ES_QUERY):
    """
    This function calls elastic search script in order to find all possible candidates for the given ELS_QUERY
    :param ES_DOMAIN: ELS_NODE:ELS_PORT
    :param ES_QUERY:  string (e.g. "Vrije University")
    :return:
    """
    total_entities = []
    for freebase_id, labels in els.search(ES_DOMAIN, ES_QUERY).items():
        my_entity = entity.Entity(ES_QUERY)
        my_entity.freebase_id = freebase_id
        my_entity.freebase_label = labels

        total_entities.append(my_entity)
    return total_entities


def log_candidates(candidates, verbose_level="info"):
    """
    Displays the freebase id and the labels found for each candidate
    :param candidates: a list with candidates
    :param verbose_level: the level of the output that will be produced
    :return:
    """
    if verbose_level == "info":
        for candidate in candidates:
            logger.info("ID: {},   LABELS: {} ".format(candidate.freebase_id, candidate.freebase_label))
    elif verbose_level == "debug":
        for candidate in candidates:
            logger.debug("ID: {},   LABELS: {} ".format(candidate.freebase_id, candidate.freebase_label))


########################################################
#              Sparql (trident) functions              #
########################################################

def get_kb_info_by_candidate(sql_domain, candidate_id):
    """
    Gets the data from trident Knowledge Base about a specific candidate
    :param sql_domain: SQL_NODE:SQL_PORT
    :param candidate_id: the freebase_id of a candidate as returned from elastic search
    :return:
    """
    # build query
    #query = build_kb_query(candidate_id, limit=10)
    query = build_kb_query_for_abstracts(candidate_id, limit=10)
    #print "query = {}".format(query)
    return sparql.sparql(sql_domain, query)


def build_kb_query(candidate_id, limit=10):
    """
    Build basic query for trident
    :param candidate_id: the freebase_id of a candidate as returned from elastic search
    :param limit: the maximum number of result that the query will find
    :return:
    """
    #remove first 3 characters with : m.
    candidate_id = candidate_id[3:]
    candidate_id = "m.{}".format(candidate_id)
    # build query
    query = 'select * where {}<http://rdf.freebase.com/ns/{}> ?p ?o{} limit 10'.format("{", candidate_id, "}")
    return query


def build_kb_query_for_abstracts(candidate_id, limit=10):
    """
    Build basic query for trident
    :param candidate_id: the freebase_id of a candidate as returned from elastic search
    :param limit: the maximum number of result that the query will find
    :return:
    """
    #remove first 3 characters with : m.
    candidate_id = candidate_id[3:]
    candidate_id = "m.{}".format(candidate_id)
    # build query
    query = "select distinct ?abstract where {} " \
            "?s <http://www.w3.org/2002/07/owl#sameAs> <http://rdf.freebase.com/ns/{}> . " \
            "?s <http://www.w3.org/2002/07/owl#sameAs> ?o ." \
            "?o <http://dbpedia.org/ontology/abstract> ?abstract." \
            "{}".format("{", candidate_id, "}")
    print "build QUERY: {}".format(query)
    return query


def get_only_english_abstract_from_json(trident_response):
    """
    Reads a json as returned from trident and returns the abstract in English
    :param trident_response: json of one candidate
    :return: list with the english abstracts of a specific candidate
    """
    english_abstacts =[]
    candidate_abstracts = trident_response["results"]["bindings"]
    for abstract in candidate_abstracts:
        if abstract["abstract"]["value"].endswith('"@en"'):
            english_abstacts.append(abstract["abstract"]["value"])

    return english_abstacts


def remove_candidates_without_abstracts(candidates):
    """
    This function is used in order to remove an object of class entity that we did not find any english abstract
    at trident.
    :param candidates: a list of objects
    :return: a list of objects
    """
    new_candidates = []
    for candidate in candidates:
        if candidate.kb_abstract:
            # if candidate has abstract append him in the new list
            new_candidates.append(candidate)

    return new_candidates


def similarity_measure(list1, list2, threeshold=0.8):
    """
    This function calculates a score based on the hamming distance between the words in the two lists.
    If the similarity between two words is above the threeshold then it is calculated as similar
    :param list1: list of stings
    :param list2: list of strings
    :param threeshold:
    :return: a score (float)
    """
    import textdistance

    score = 0

    for word1 in list1:
        for word2 in list2:
            if textdistance.hamming.normalized_similarity(word1, word2) > threeshold:
                # word is similar (above the threeshold)
                score += 1
    # calculate the normalized score
    score_normalized = float(score)/len(list1)

    return score_normalized


def main():
    """
    Main function
    :return:
    """
    # set loggers
    set_logger(stream_level="error", file_level="info", log_filename="file1.log")
    preprocessing.set_logger(stream_level="error", file_level="error", log_filename="file2.log")

    try:
        _, ELS_DOMAIN, SQL_DOMAIN, WARC_FILE = sys.argv
    except Exception as e:
        print('Usage: python elasticsearch.py DOMAIN QUERY')
        sys.exit(0)

    # for each word in each document find the potential candidates by using elastic search.
    # For each candidate query trident KB and keep only the english abstracts from the results
    for warc_id, document_results in preprocessing.main(WARC_FILE):
        logger.info("============  DOCUMENT  ==============")
        for doc_entity in document_results:
            logger.debug("===============  Elastic search ==================")
            logger.debug("Candidates for [{}]".format(doc_entity))
            candidates = find_candidates(ELS_DOMAIN, doc_entity)
            log_candidates(candidates, "debug")
            logger.debug("================End of ES -- Start of Trident=================")
            for candidate in candidates:
                logger.debug("QUERY Trident for candidate: {} with id: {}".format(candidate.name, candidate.freebase_id))
                trident_response = get_kb_info_by_candidate(SQL_DOMAIN, candidate.freebase_id)
                #logger.info(json.dumps(trident_response, indent=2))
                # extract only English abstract
                candidate.kb_abstract = get_only_english_abstract_from_json(trident_response)
                logger.debug("Abstract from trident: {}\n".format(candidate.kb_abstract))
            logger.debug("===============  END of Trident ==================")
            candidates = remove_candidates_without_abstracts(candidates)
            # if candidates not found (or removed) move to the next word
            if not candidates:
                continue
            logger.info("===============  Candidates ==================")
            # initialise the best candidate
            candidate_with_best_score = candidates[0]
            for candidate in candidates:
                # concatenate the english abstract of one candidate
                abstract = " ".join(candidate.kb_abstract)
                # extract the nouns from the abstract
                candidate.kb_nouns = preprocessing.extract_nouns_from_text(abstract)
                candidate.similarity_score = similarity_measure(document_results, candidate.kb_nouns)
                logger.info("Candidate_id: {},   label: {},   Abstract:  \n{}\n\n Nouns: {}\n\n Score: {}\n\n\n".format(
                    candidate.freebase_id,
                    candidate.freebase_label,
                    candidate.kb_abstract,
                    candidate.kb_nouns,
                    candidate.similarity_score))
                # check the best score from candidates
                if candidate.similarity_score > candidate_with_best_score.similarity_score:
                    # change best candidate
                    candidate_with_best_score = candidate

            logger.info(" -------------   Candidate with BEST score for {} -------------  ".format(doc_entity))
            logger.info("Candidate_id: {},   label: {},   Abstract:  \n{}\n\n Nouns: {}\n\n Score: {}\n\n\n".format(
                candidate_with_best_score.freebase_id,
                candidate_with_best_score.freebase_label,
                candidate_with_best_score.kb_abstract,
                candidate_with_best_score.kb_nouns,
                candidate_with_best_score.similarity_score))

            print "{}       {}    {}".format(warc_id, doc_entity, candidate_with_best_score.freebase_id)


if __name__ == '__main__':
    main()




