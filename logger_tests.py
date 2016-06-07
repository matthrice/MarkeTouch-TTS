import logging
from logging.handlers import RotatingFileHandler
import time

logging.basicConfig(filemode='a', 
						format='%(asctime)s %(name)s %(levelname)s %(message)s',
						datefmt='%H:%M:%S',
						level=logging.DEBUG)

def test_createRotatingLog(path):
	#initiates logging session
	logger = logging.getLogger("TTS_test")

	#defines handler for byte size
	#will roll over after 100 mb, will max out at 10 backup files
	sizeHandler = RotatingFileHandler(path, maxBytes=20, 
								  backupCount=5)
	logger.addHandler(sizeHandler)

	for i in (3, 2, 1):
		logger.info("This is test log line - %s" % i)
		time.sleep(5)

log_file = "test.log"
test_createRotatingLog(log_file)



