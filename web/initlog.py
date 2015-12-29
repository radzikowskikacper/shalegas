##
# @file web/initlog.py
# @brief SweetSpot init logger

import logging, os
import logging.handlers

LOG_FILE_DIR = os.environ['SWEETSPOT_LOG_DIR']
LOG_FILE_NAME = 'sweetspot.log'

#TODO: LOG_FILE_DIR from ENV SWEETSPOT_LOG_DIR
#TODO: set ENV SWEETSPOT_LOG_DIR in debian package on /var/log

def init_logging():
    logger = logging.getLogger('sweetspot')
    
    if 'SWEETSPOT_LOG_LEVEL' in os.environ:
        logger.setLevel(getattr(logging, os.environ['SWEETSPOT_LOG_LEVEL'], logging.INFO))
    else:
        logger.setLevel(logging.INFO)
        
    handlerFile = logging.handlers.RotatingFileHandler( LOG_FILE_DIR + '/' + LOG_FILE_NAME, "a", 1024*1024, 5)
    handlerFile.setLevel(logging.DEBUG)
    handlerFile.setFormatter( logging.Formatter("%(asctime)s %(levelname)s %(name)s - %(message)s") )
    logger.addHandler(handlerFile)

global loggingInitDone
loggingInitDone=False
if not loggingInitDone:
    init_logging()
    logger = logging.getLogger('sweetspot.initlog')
    logger.info('Server started')
    loggingInitDone=True
