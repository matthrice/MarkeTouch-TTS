import requests
import wave
import pyaudio
import os

class Watson:

	#streaming parameters
	RATE = 22050
	SAMPWIDTH = 2
	NCHANNELS = 1

	#initializes parameters for authorization and conversion
	def __init__(self, username, password, voice, 
				 url, chunk, accept):
		self.username = username
		self.password = password
		self.voice = voice
		self.url = url
		self.chunk = int(chunk)
		self.accept = accept

	#function to convert text to speech file
	#REQUIRES: text is valid for conversion, filename ends in .wav
	#EFFECTS: places a .wav file in the project folder
	def download(self, text, filename, path):

		#requests gets response using parameters for authorization and audio format
		#stream=True allows it to be streamed as well
		#verify=False ignores SSL certification
		r = requests.get(self.url + "/v1/synthesize",
                           auth=(self.username, self.password),
                           params={'text': text, 'voice': self.voice, 'accept': self.accept},
                           verify=False
                           )
		#ensures path and directory exist
		if not os.path.exists(path):
			os.makedirs(path)

		#opens filename from stream and saves it into filename
		#'wb' indicates file is opened for writing in binary mode
		#joins path and filename
		with open(os.path.join(path, filename), 'wb') as fd:
			for chunk in r.iter_content(self.chunk):
				fd.write(chunk)

	#reads in input and determines if more than one file is needed to download
	#REQUIRES: Text is in format of *LANGUAGE text
	#EFFECTS: Produces a single file if no language change, or produces several 
	#files with a number extension marking their order if text uses multiple
	#languages
	def writeFiles(self, text, filename, path):
		print("\nConverting text.\n")

		#saves english voice specification
		english = self.voice
		#creates a counter for the filenames
		count = 0
		#creates an extension for the filename
		extension = ""
		if self.accept == "audio/wav":
			extension = ".wav"
		elif self.accept == "audio/ogg;codecs=opus":
			extension = ".ogg"

		#splits the strings into a list, separated by the symbol (*)
		text = text[1:]
		stringList = text.split('*')
		#iterates through the strings in the list
		#each should begin with a specification of language
		for string in stringList:
			count += 1
			#splits the string from the language variable
			a, b = string.split(" ", 1)
			#creates a spanish file 
			if a == "Spanish":
				self.voice = "es-US_SofiaVoice"
				#checks if no language change, if so leaves off count
				if len(stringList) == 1:
					self.download(b, filename + extension, path)
				else:
					self.download(b, filename + str(count) + extension, path)
			#creates an english file
			elif a == "English":
				self.voice = english
				#checks if no language change, if so leaves off count
				if len(stringList) == 1:
					self.download(b, filename + extension, path)
				else:
					self.download(b, filename + str(count) + extension, path)

	#streams the file using pyaudio
	#REQUIRES: stream is a valid instantiation of pyaudio stream
	#EFFECTS: creates an output stream
	def stream(self, text, stream):
		
		#request is made for the speech audio file, recieves response
		#stream is set to true so the data will not be downloaded at once
		r = requests.get(self.url + "/v1/synthesize",
                           auth=(self.username, self.password),
                           params={'text': text, 'voice': self.voice, 'accept': self.accept},
                           stream=True, verify=False,
                           )


		#creates empty bytes variable and byte counter
		dataToRead = b''
		bytesRead = 0
		#iterates through the response, one byte at a time
		for data in r.iter_content(1):
			#each iteration adds data to empty variables
			dataToRead += data
			bytesRead += 1
			#once dataToRead reaches the chunk size, the chunk is written into the stream
			#dataToRead is emptied and a new chunk is read
			if bytesRead % self.chunk == 0:
				stream.write(dataToRead)
				dataToRead = b''


	def playFiles(self, text):
		print("\nStreaming text.\n")

		p = pyaudio.PyAudio()

		#opens stream using pyaudio
		stream = p.open(format=p.get_format_from_width(self.SAMPWIDTH),
						channels=self.NCHANNELS,
						rate=self.RATE,
						output=True)

		#saves english voice specification
		english = self.voice
		#creates a counter for the filenames
		count = 0

		text = text[1:]
		stringList = text.split('*')
		#iterates through the strings in the list
		#each should begin with a specification of language
		for string in stringList:
			count += 1
			#splits the string from the language variable
			a, b = string.split(" ", 1)
			#streams a spanish file 
			if a == "Spanish":
				self.voice = "es-US_SofiaVoice"
				self.stream(b, stream)
			#streams an english file
			elif a == "English":
				self.voice = english
				self.stream(b, stream)


		#stop stream
		stream.stop_stream()
		stream.close()

		#closes pyaudio
		p.terminate()





#for more: http://docs.python-requests.org/en/master/user/quickstart/
