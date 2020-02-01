import sys
import logging
import gzip
from bs4 import BeautifulSoup

#  define logger as global variable
logger = logging.getLogger(__name__)

# define KEYNAME for records
KEYNAME = "WARC-TREC-ID"


def prerequisites():
    import nltk
    nltk.download('punkt')

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
########################################################
########################################################


def find_labels(payload, labels):
    key = None
    for line in payload.splitlines():
        if line.startswith(KEYNAME):
            key = line.split(': ')[1]
            break
    for label, freebase_id in labels.items():
        if key and (label in payload):
            yield key, label, freebase_id


def find_id(payload):
    """
    This function finds the WARC-TREC-ID
    :param payload:
    :return: a string with the WARC-TREC-ID
    """
    key = None
    for line in payload.splitlines():
        if line.startswith(KEYNAME):
            key = line.split(': ')[1]
            break
    return key


def split_records(stream):
    payload = ''
    for line in stream:
        if line.strip() == "WARC/1.0":
            yield payload
            payload = ''
        else:
            payload += line


def remove_code_blocks(text):
    """
    This function removes all blocs that starts with <!-- and ends at //-->
    :param text: the text that will be processed
    :return: a list without code blocks
    """
    textlines = text.splitlines()
    new_lines = []
    code_block = False
    for line in textlines:
        if line.startswith("<!--"):
            code_block = True
        elif line.startswith("//-->"):
            code_block = False
        elif code_block is False:
            new_lines.append(line)

    return new_lines


def tokenizer(text_string):
    """
    This function uses nltk library and stanford tokenizer in order to split a string into tokens
    :param text_string:
    :return: a list with tokens
    """
    from nltk import word_tokenize
    tokens = word_tokenize(text_string)
    return tokens


def split_headers(doc):
    """
    Returns only the headers and the body without the WARC and the connection variables/info
    :param doc: string
    :return: headers, body
    """
    if "Content-Type: text/html; charset=UTF-8" in doc:
        headers, body = doc.split("Content-Type: text/html; charset=UTF-8")
    else:
        logger.warning("Missed document in split headers")
        logger.debug("Document does not have Content-Type value")

    return headers, body



if __name__ == "__main__":

    # set logger
    set_logger(stream_level="error", file_level="info", log_filename="file1.log")

    #   nltk prerequisites
    #prerequisites()

    # read input (filename)
    logger.debug("Read input (filename)")
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    else:
        logger.error("Please provide a filename as input")
        raise IOError

    warcfile = gzip.open(sys.argv[1], "rt", errors="ignore")
    record_no = 0
    max_records = 4
    for record in split_records(warcfile):
        if record_no < max_records:
            record_no += 1
            logger.debug("record_no < {}".format(max_records))

            logger.info("----------- Document No {}---------------".format(record_no))
            if not record:      # if empty
                logger.debug("EMPTY")
                continue
            if record_no == 2 or record_no == 3:
                continue
            soup = BeautifulSoup(record, "lxml")
            logger.info(soup.text)
            logger.info("==================================")
            # split headers from body
            headers, body = split_headers(soup.text)
            # # HEADERS preprocessing
            warc_id = find_id(headers)
            if not warc_id:  # if empty
                logger.debug("No ID. This file will be skipped")
                continue
            logger.info("ID: {}".format(warc_id))
            # # BODY preprocessing
            # remove code blocks
            lines = remove_code_blocks(body)
            # join all lines together
            body = " ".join(lines)
            # tokenize
            tokens = tokenizer(body)
            for token in tokens:
                logger.info(token)
            logger.info("--------------------------")
            logger.info("--------------------------")
        else:
            logger.debug("record_no = {}".format(max_records))
            logger.debug("Exiting...")
            exit(0)




#               python3 main.py "../../../sample.warc.gz"
