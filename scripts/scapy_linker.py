import sys
import logging

from scapy_preprocessing import preprocess
import linker
import preprocessing


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


def main():
    """
    Main function
    :return:
    """
    # set loggers
    set_logger(stream_level="error", file_level="info", log_filename="file_scapy.log")

    try:
        _, ELS_DOMAIN, SQL_DOMAIN, WARC_FILE = sys.argv
    except Exception as e:
        print('Usage: python elasticsearch.py DOMAIN QUERY')
        sys.exit(0)

    # for each word in each document find the potential candidates by using elastic search.
    # For each candidate query trident KB and keep only the english abstracts from the results
    for warc_id, document_entity in preprocess(WARC_FILE):
        doc_entity = document_entity[0]
        logger.debug("===============  Elastic search ==================")
        logger.debug("Candidates for [{}]".format(doc_entity))
        candidates = linker.find_candidates(ELS_DOMAIN, doc_entity)
        linker.log_candidates(candidates, "debug")
        logger.debug("================End of ES -- Start of Trident=================")
        for candidate in candidates:
            logger.debug("QUERY Trident for candidate: {} with id: {}".format(candidate.name, candidate.freebase_id))
            trident_response = linker.get_kb_info_by_candidate(SQL_DOMAIN, candidate.freebase_id)
            #logger.info(json.dumps(trident_response, indent=2))
            # extract only English abstract
            candidate.kb_abstract = linker.get_only_english_abstract_from_json(trident_response)
            logger.debug("Abstract from trident: {}\n".format(candidate.kb_abstract))
        logger.debug("===============  END of Trident ==================")
        candidates = linker.remove_candidates_without_abstracts(candidates)
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
            candidate.similarity_score = preprocessing.similarity_measure(document_results, candidate.kb_nouns)
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

        print "{}\t{}\t{}".format(warc_id, doc_entity, candidate_with_best_score.freebase_id)


if __name__ == '__main__':
    main()