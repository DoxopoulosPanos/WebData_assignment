import sys
import logging
import gzip
import re
from bs4 import BeautifulSoup

#  define logger as global variable
logger = logging.getLogger(__name__)

# define KEYNAME for records
KEYNAME = "WARC-TREC-ID"

# install nltk prerequisites
INSTALL_PREREQUISITES = False


def prerequisites():
    """
    Install prerequisites for nltk modules
    this function is executed only if INSTALL_PREREQUISITES=True
    :return: None
    """
    import nltk
    nltk.download('punkt')
    nltk.download('stopwords')
    nltk.download('wordnet')
    nltk.download('averaged_perceptron_tagger')


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


########################################################
#             nlp preprocessing helpers                #
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
    This function uses nltk library in order to split a string into tokens
    :param text_string:
    :return: a list with tokens
    """
    from nltk import word_tokenize
    tokens = word_tokenize(text_string)
    return tokens


def stemming(word_tokens):
    """
    This function uses nltk library in order to stem the words
    :param word_tokens:
    :return:
    """
    from nltk.stem import PorterStemmer

    ps = PorterStemmer()
    for word_token in word_tokens:
        yield ps.stem(word_token)


def lemmatization(word_tokens):
    """
    This function uses nltk library in order to lemma the words
    :param word_tokens:
    :return:
    """
    from nltk.stem import WordNetLemmatizer

    lemmatizer = WordNetLemmatizer()
    for word_token in word_tokens:
        yield lemmatizer.lemmatize(word_token)


def remove_stop_words(tagged):
    """
    This function is used in order to remove stopwords (e.g. "is", "a"), by using nltk library
    :param tagged: tokens as they retrieved from pos tagger (tuples)
    :return: a list with tokens (without the stop words)
    """
    from nltk.corpus import stopwords
    # define stop words
    stop_words = set(stopwords.words('english'))
    # filter text
    filtered_sentence = [w for w in tagged if w[0] not in stop_words]           # w = (word_token, pos)

    return filtered_sentence


def remove_alphanumeric(word_token):
    """
    This function is used in order to remove alphanumeric from tokens (by using library re - regular expressions)
    :param word_token:
    :return:
    """
    pattern = re.compile('[\W_]+')
    return pattern.sub('', word_token)


def remove_number_from_string(word_token):
    """
    This function is used in order to remove numbers from token
    :param word_token:
    :return:
    """
    return ''.join([i for i in word_token if not i.isdigit()])


def pos_tagging(word_tokens):
    """
    This function uses nltk library in order to perform POS tagging
    :param word_tokens:
    :return: a tuple
    """
    from nltk import pos_tag
    return pos_tag(word_tokens)


def remove_hex_from_string(word_token):
    """
    Removes hex number from string. Looks for patterns with number followed by capital letter [A-F]
    :param word_token:
    :return: string
    """
    return re.sub(r'[0-9][A-F]', r'', word_token)


def group_consecutive_groups(tagged):
    """
    group consecutive groups of words with the same NNP tag
    :param tagged: result of POS (tuples)
    :return: strings
    """
    from itertools import groupby
    groups = groupby(tagged, key=lambda x: x[1])  # Group by tags
    names = [[w for w, _ in words] for tag, words in groups if tag == "NNP"]
    names = [" ".join(name) for name in names if len(name) >= 2]

    return names


########################################################
########################################################


def main():
    """
    Main function
    :return:
    """
    warcfile = gzip.open(sys.argv[1], "rt", errors="ignore")
    record_no = 0
    max_records = 4
    for record in split_records(warcfile):
        if record_no < max_records:
            record_no += 1
            logger.debug("record_no < {}".format(max_records))

            logger.info("----------- Document No {}---------------".format(record_no))
            if not record:  # if empty
                logger.debug("EMPTY")
                continue
            if record_no == 2 or record_no == 3:
                continue
            soup = BeautifulSoup(record, "lxml")
            #logger.info(soup.text)
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
            tokens = [remove_hex_from_string(x) for x in tokens]
            logger.info("======================+++++++++++++++++++++++++++++++")

            tokens_without_numbers = []
            for token in lemmatization(tokens):          # implement stemming
                token_without_alpha = remove_alphanumeric(token)  # remove alphanumeric
                token_without_numbers = remove_number_from_string(token_without_alpha)
                if token_without_numbers is not "":         # remove empty strings
                    tokens_without_numbers.append(token_without_numbers)
            logger.info("--------------------------")

            # ------------------------------------
            # POS tagging
            tagged = pos_tagging(tokens_without_numbers)
            groups = group_consecutive_groups(tagged)

            # ------------------------------------

            # stop word removal
            tokens_after_stop_word_removal = []

            for tagged_word in remove_stop_words(tagged):         # remove stop words (x[0] = word , x[1]= POS)
                if len(tagged_word[0]) > 2:               # remove words with length < 3
                    tokens_after_stop_word_removal.append(tagged_word)

            del token_without_numbers

            for word in tokens_after_stop_word_removal:
                logger.info(word)
            logger.info('====dddddddddddddddddddddddddddd===================================')
            for tagged_word in groups:
                logger.info(tagged_word)            # all are NNP

            del tokens_after_stop_word_removal

            logger.info("--------------------------")
            logger.info("--------------------------")
        else:
            logger.debug("record_no = {}".format(max_records))
            logger.debug("Exiting...")
            exit(0)


if __name__ == "__main__":

    # set logger
    set_logger(stream_level="error", file_level="info", log_filename="file1.log")

    #   nltk prerequisites
    if INSTALL_PREREQUISITES:
        logger.debug("Install prerequisites for nltk...")
        prerequisites()
        logger.debug("Installation of nltk prerequisites completed")

    # read input (filename)
    logger.debug("Read input (filename)")
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    else:
        logger.error("Please provide a filename as input")
        raise IOError

    main()


    # experiments
    # from nltk.tag import StanfordNERTagger
    # st = StanfordNERTagger('exist-stanford-ner/resources/classifiers/english.all.3class.distsim.crf.ser.gz',
    #                        'exist-stanford-ner/java/lib/stanford-ner-2015-04-20.jar', encoding='utf-8')
    # classified_text = st.tag(tokenized_text)
#               python3 preprocessing.py "../../../sample.warc.gz"

