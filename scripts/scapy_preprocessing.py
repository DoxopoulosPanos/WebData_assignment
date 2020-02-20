import sys
import logging
import gzip
import re
from bs4 import BeautifulSoup
from bs4 import Comment

#  define logger as global variable
import linker
import scapy_entity

logger = logging.getLogger(__name__)

# define KEYNAME for records
KEYNAME = "WARC-TREC-ID"

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
########################################################


########################################################
#                parser helpers                  #
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


def get_text_from_webpage(html):
    soup = BeautifulSoup(html, "html5lib")

    unwanted_fields = [soup.find_all('script'),
                       soup.find_all('style'),
                       soup.find_all('meta'),
                       soup.find_all('noscript'),
                       soup.find_all(text=lambda text:isinstance(text, Comment))]

    for field in unwanted_fields:
        [x.extract() for x in field]
    return soup


def clear_text(text):
    text = text.replace("\t", ". ")
    text = text.replace("\n", " ")

    return text


def split_headers(doc):
    """
    Returns only the headers and the body without the WARC and the connection variables/info
    :param doc: string
    :return: headers, body
    """
    if "Content-Type:" in doc:
        try:
            headers, _, body = doc.split("Content-Type:")
        except:
            return None, None
        # removing the Content-Type value
        # split at the first new line and take the second value
        body = body.split("\n", 1)[1]
    else:
        logger.warning("Missed the following document in split headers")
        logger.warning(doc)
        logger.debug("Document does not have Content-Type value")
        return None, None

    return headers, body


##################################
#    SPACY                       #
##################################
# spacy types are many but I only keep those that could be possibly helpfull
spacy_ner_types = ["PERSON", "NORP", "FAC", "ORG", "GPE", "LOC", "PRODUCT", "EVENT", "WORK_OF_ART", "LANGUAGE"] # "DATE"


def spacy_ner(text):
    """
    Named Entity Recognition.
    :param text: text decoded in utf-8
    :return:
    """
    import spacy
    nlp = spacy.load('en_core_web_sm')

    doc = nlp(text)

    for ent in doc.ents:
        # yield the entity only if its type exists in the predefined list
        if ent.label_ in spacy_ner_types:
            try:
                yield ent.text.encode("utf-8"), ent.label_.encode("utf-8")
            except:
                yield ent.text, ent.label_

        #print(ent.text, ent.start_char, ent.end_char, ent.label_)


def preprocess(warc_filename):
    """
    Main function
    :param warc_filename: the path to warc file
    :return:
    """
    warcfile = gzip.open(warc_filename, "rt")
    record_no = 0
    max_records = 20  #TODO: change
    for record in split_records(warcfile):
        if record_no < max_records:
            record_no += 1
            logger.debug("record_no < {}".format(max_records))

            logger.info("----------- Document No {}---------------".format(record_no))
            if not record:  # if empty
                logger.debug("EMPTY")
                continue

            soup = get_text_from_webpage(record)
            logger.info("==================================")
            # split headers from body
            headers, body = split_headers(soup.text)

            # if split could not be achieved go to the nect record
            if body is None:
                continue

            # # HEADERS preprocessing
            warc_id = find_id(headers)
            if not warc_id:  # if empty
                logger.debug("No ID. This file will be skipped")
                continue
            logger.info("ID: {}".format(warc_id))

            # # preprocessing
            body = clear_text(body)
            for entity in spacy_ner(body):
                print entity
                mention = scapy_entity.Mention(name=entity[0], warc_id=warc_id)
                mention.ner_label = entity[1]
                logger.info(mention)
                continue
                #yield mention


if __name__ == "__main__":

    # set logger
    set_logger(stream_level="info", file_level="info", log_filename="test3.log")

    # read input (filename)
    logger.debug("Read input (filename)")
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    else:
        logger.error("Please provide a filename as input")
        raise IOError

    preprocess(filename)
