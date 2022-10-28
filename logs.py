import logging

logger = logging.getLogger("Node")
# Create a handler
c_handler = logging.StreamHandler()
c_format = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
c_handler.setFormatter(c_format)
# link handler to logger
logger.addHandler(c_handler)
# Set logging level to the logger
logger.setLevel(logging.INFO)  # <-- THIS!

def print_log(message: str, level: int):
    if level == 1:
        logger.info(msg=message)