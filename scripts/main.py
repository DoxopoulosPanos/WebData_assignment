import sys
import logging
import warc

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


def set_logger(level="info"):
    """
    This function is used in order to set the level of the global logger
    :param level: logging level (e.g. logging.DEBUG)
    :return:
    """
    # find level
    log_level = map_logging_level(level)
    # create console handler with a higher log level
    handler = logging.StreamHandler()
    file_handler = logging.FileHandler("file.log")
    handler.setLevel(log_level)
    file_handler.setLevel(log_level)
    # create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    # add the handlers to the logger
    logger.addHandler(handler)
    logger.addHandler(file_handler)
########################################################
########################################################


if __name__ == "__main__":

    # set logger
    set_logger(level="info")

    # read input (filename)
    logger.debug("Read input (filename)")
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    else:
        logger.error("Please provide a filename as input")
        raise IOError

    records = warc.WARCFile(filename, "rb")
    record_no = 2
    for record in records:
        if record_no > 0:
            print record["Content-Type"]
            print record.payload.read()
            print "--------------------------"
            print "--------------------------"
        record_no -= 1



#               python3 main.py "../../../sample.warc.gz"
