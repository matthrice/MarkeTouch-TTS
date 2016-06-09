import unittest
import requests
import glob, os
import main
import logging
from unittest.mock import patch
from watson import Watson

URL = 'https://stream.watsonplatform.net/text-to-speech/api'
PASSWORD = 'QiVBWYF2uBlJ'
USERNAME = 'be745e3d-8ee2-47b6-806a-cee0ac2a6683'
CHUNK_SIZE = 1024

#simple logger to act as parameter for the functions
logging.basicConfig(filename='maintest.log',level=30)
Logger = logging.getLogger("main_test_log")
#main test case using unittest module
#class inherits the Test Case from the module
class MainTestCase(unittest.TestCase):


	#test for the default constructor of the watson class
	def test_watson_init(self):
		#creates a simple watson object with junk class members
		watson = Watson('username_1', 'password_1', 'voice_1',
						'url_1', '1024', 'accept_1')
		#tests each case of initialization using assertEqual
		#provided for by unittest
		self.assertEqual(watson.username, 'username_1')
		self.assertEqual(watson.password, 'password_1')
		self.assertEqual(watson.voice, 'voice_1')
		self.assertEqual(watson.url, 'url_1')
		self.assertEqual(watson.chunk, 1024)
		self.assertEqual(watson.accept, 'accept_1')

	#tests the request module
	#part of the download() and stream() functions
	'''
	def test_download_request(self):

		requests.packages.urllib3.disable_warnings()

		#create a working watson object
		watson = Watson(USERNAME, PASSWORD, "en-US_AllisonVoice", URL, CHUNK_SIZE, 'audio/wav')

		text = 'Request test'

		r = requests.get(watson.url + "/v1/synthesize",
                           auth=(watson.username, watson.password),
                           params={'text': text, 'voice': watson.voice, 'accept': watson.accept},
                           verify=False
                           )

		self.assertEqual(r.status_code, requests.codes.ok,
						 "Bad request, invalid response status code")


	def test_write_files(self):

		text0 = "*English hello."
		text1 = "*Spanish hola, como estas?"
		text2 = "*English does this work? *Spanish Este es una prueba. *English this is a test"

		watson = Watson(USERNAME, PASSWORD, 'en-US_MichaelVoice', URL,
						CHUNK_SIZE, "audio/wav")

		watson.writeFiles(text0, "text0", "wavfiles")
		watson.writeFiles(text1, "text1", "wavfiles")
		watson.writeFiles(text2, "text2", "wavfiles")

		self.assertTrue(os.path.exists("wavfiles/text0.wav"))
		self.assertTrue(os.path.exists("wavfiles/text1.wav"))
		self.assertTrue(os.path.exists("wavfiles/text21.wav"))
		self.assertTrue(os.path.exists("wavfiles/text22.wav"))
		self.assertTrue(os.path.exists("wavfiles/text23.wav"))

		filelist = [f for f in os.listdir("wavfiles") if f.endswith(".wav")]
		os.chdir("wavfiles")
		for f in filelist:
			os.remove(f)

		'''

	def test_valid_filename(self):

		filename1 = "hello"
		filename2 = "&$(#what"
		filename3 = "himynameis:paul"
		filename4 = "hi.my.name.is.Matt"

		self.assertTrue(main.validFilename(filename1))
		self.assertTrue(main.validFilename(filename2))
		self.assertFalse(main.validFilename(filename3))
		self.assertFalse(main.validFilename(filename4))

	def test_request_voiceID(self):

		print("enter 1: ")
		voiceID1 = main.requestVoiceID(Logger)
		print("enter 2: ")
		voiceID2 = main.requestVoiceID(Logger)
		print("enter 0: ")
		voiceID3 = main.requestVoiceID(Logger)


		self.assertEqual(voiceID1, 'en-US_MichaelVoice')
		self.assertNotEqual(voiceID2, 'en-US_MichaelVoice')
		self.assertEqual(voiceID2, 'en-US_AllisonVoice')
		self.assertEqual(voiceID3, 'en-US_AllisonVoice')

	def test_request_format(self):
		print("enter 1: ")
		format1 = main.requestFormat(Logger)
		print("enter 2: ")
		format2 = main.requestFormat(Logger)
		print("enter 3: ")
		format3 = main.requestFormat(Logger)

		self.assertEqual(format1, "audio/wav")
		self.assertEqual(format2, "audio/ogg;codecs=opus")
		self.assertEqual(format3, "audio/ogg;codecs=opus")









if __name__ == '__main__':
	unittest.main()
