import requests
import pyaudio
import os

from transcript import Transcript

## WATSON CLASS ##

#Watson Class holds information for audio synthesis
#Holds credentials for HTTP requests and transcript info
#Contains functions to write and play the audio
class Watson():

	#streaming parameters
	RATE = 22050
	SAMPWIDTH = 2
	NCHANNELS = 1

	#download parameter
	CHUNK_SIZE = 1024
	GOOD_STATUS = 200

	## CONSTRUCTOR ##
	#initializes parameters for authorization and conversion
	def __init__(self, username, password, url, transcript):
		self.username = username
		self.password = password
		self.url = url
		self.chunk = self.CHUNK_SIZE
		self.transcript = transcript


	#function to change self.voice if user wants multiple languages in one message
	#takes a string and parses the first word of the string. If it matches a
	#watson supported language identifier, self.voice is changed accordingly
	#If no change, voice is kept in default language
	def changeVoice(self, string):
		defaultLang = self.transcript.getVoice()

		#Checks for a language change that is allowed in multiple files
		#All the available watson languages listed below
		#if a new language is chosen, self.voice is changed and
		#the text is split to take out the language identifier

		#Spanish (North American dialect), female
		if string[:16] == "es-US_SofiaVoice":
			self.transcript.voice = "es-US_SofiaVoice"
			a, b = string.split(" ", 1)

		#German, female
		elif string[:17] == "de-DE_BirgitVoice":
			self.transcript.voice = "de-DE_BirgitVoice"
			a, b = string.split(" ", 1)

		#German, male
		elif string[:17] == "de-DE_DieterVoice":
			self.transcript.voice = "de-DE_DieterVoice"
			a, b = string.split(" ", 1)

		#English (British dialect), female
		elif string[:15] == "en-GB_KateVoice":
			self.transcript.voice = "en-GB_KateVoice"
			a, b = string.split(" ", 1)

		#English (US dialect), female
		elif string[:18] == "en-US_AllisonVoice":
			self.transcript.voice = "en-US_AllisonVoice"
			a, b = string.split(" ", 1)

		#English (US dialect), female
		elif string[:15] == "en-US_LisaVoice":
			self.transcript.voice = "en-US_LisaVoice"
			a, b = string.split(" ", 1)

		#Spanish (Castilian dialect), male
		elif string[:18] == "es-ES_EnriqueVoice":
			self.transcript.voice = "es-ES_EnriqueVoice"
			a, b = string.split(" ", 1)

		#Spanish (Castilian dialect), female
		elif string[:16] == "es-ES_LauraVoice":
			self.transcript.voice = "es-ES_LauraVoice"
			a, b = string.split(" ", 1)

		#French, female
		elif string[:16] == "fr-FR_ReneeVoice":
			self.transcript.voice = "fr-FR_ReneeVoice"
			a, b = string.split(" ", 1)

		#Italian, female
		elif string[:20] == "it-IT_FrancescaVoice":
			self.transcript.voice = "it-IT_FrancescaVoice"
			a, b = string.split(" ", 1)

		#Japanese, female
		elif string[:14] == "ja-JP_EmiVoice":
			self.transcript.voice = "ja-JP_EmiVoice"
			a, b = string.split(" ", 1)

		#Brazilian Portuguese, female
		elif string[:18] == "pt-BR_IsabelaVoice":
			self.transcript.voice = "pt-BR_IsabelaVoice"
			a, b = string.split(" ", 1)

		#default voice, for switching back
		else:
			self.transcript.voice = defaultLang
			#doesn't split text because there's no language change identifier
			b = string

		#returns the rest of the string after self.voice is changed
		return b


	def download(self, text, filename):
		# requests gets response using parameters for authorization and audio format
		# stream=True allows it to be streamed as well
		# verify=False ignores SSL certification

		# initializes values from transcript to make code simpler
		voice = self.transcript.getVoice()
		accept = self.transcript.getAccept()  # returns a dictionary
		path = self.transcript.getWavFilePath()
		#replace \\ with \, pyodbc interprets the paths incorrectly
		path = path.replace("\\\\", "\\")

		#create HTTP request object
		r = requests.get(self.url + "/v1/synthesize",
						 auth=(self.username, self.password),
						 params={'text': text, 'voice': voice, 'accept': accept},
						 verify=False
						 )

		#Checks the status for a good http response
		#If not good (200), sets the error and status code accordingly
		if r.status_code != self.GOOD_STATUS:
			self.transcript.setStatus(self.transcript.STATUS_ERROR)
			self.transcript.setError(r.status_code)
			#returns the error in the same format as a real listElement
			#Each list element will be checked for "Error" later
			return ["Error", str(r.status_code)]

		#If the function continues, checks for path. Makes it if nonexistent
		if not os.path.exists(path):
			os.makedirs(path)

		# opens filename from stream and saves it into filename
		# 'wb' indicates file is opened for writing in binary mode
		# joins path and filename
		with open(os.path.join(path, filename), 'wb') as fd:
			for chunk in r.iter_content(self.chunk):
				fd.write(chunk)

		# extension lenght of file = 4 (". w a v")
		listElement = [path, filename[:-4]]

		return listElement

	#reads in input and determines if more than one file is needed to download
	#REQUIRES: Text is in format of *LANGUAGE text
	#EFFECTS: Produces a single file if no language change, or produces several
	#files with a number extension marking their order if text uses multiple
	#languages
	def writeFiles(self):

		#Command line indicator that the synthesis process is occuring
		print("\nConverting text.\n")


		#saves english voice specification
		text = self.transcript.getTranscriptText()
		#creates a counter for the filenames
		count = 0
		#creates an extension for the filename
		extension = ""
		if self.transcript.getAccept() == "audio/wav":
			extension = ".wav"
		else:
			extension = ".ogg"

		#empty list for storing filenames
		#will be used later in main for conversion to vox
		fileList = []

		#splits the strings into a list, separated by the symbol (*)
		stringList = text.split('*')
		#iterates through the strings in the list
		#each should begin with a specification of language
		if len(stringList) == 1:
			#recieves list element from download function and appends it
			f = self.download(stringList[0],
							  self.transcript.getFileName() + extension)
			fileList.append(f)

		#process occurs differently if there's a split in the text string
		#first checks for language change, then downloads
		elif len(stringList) > 1:
			for string in stringList:
				count += 1

				b = self.changeVoice(string)
				#downloads the file with an extension of its count
				#appends the files in order in fileList
				f = self.download(b, self.transcript.getFileName() + str(count) + extension)
				fileList.append(f)


		#returns a list of all files written
		#returns them as a list of 2 element lists
		#each element contains both the filename and its path
		#useful later for vox conversion and merging
		return fileList

	#streams the file using pyaudio
	#REQUIRES: stream is a valid instantiation of pyaudio stream
	#EFFECTS: creates an output stream
	def stream(self, stream):

		#initializing here to make code simpler
		text = self.transcript.getTranscriptText()
		voice = self.transcript.getVoice()
		accept = self.transcript.getAccept()


		#request is made for the speech audio file, recieves response
		#stream is set to true so the data will not be downloaded at once
		r = requests.get(self.url + "/v1/synthesize",
                           auth=(self.username, self.password),
                           params={'text': text, 'voice': voice,'accept': accept},
                           verify=False
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

	#Plays files using the stream method above and the pyaudio module
	#Requires a wav type audio file
	def playFiles(self):
		print("\nStreaming text.\n")

		p = pyaudio.PyAudio()

		#opens stream using pyaudio
		stream = p.open(format=p.get_format_from_width(self.SAMPWIDTH),
						channels=self.NCHANNELS,
						rate=self.RATE,
						output=True)

		#saves english voice specification
		english = self.transcript.getVoice()
		text = self.transcript.getTranscriptText()
		#creates a counter for the filenames
		count = 0


		stringList = text.split('*')
		#iterates through the strings in the list
		#each should begin with a specification of language
		if len(stringList) == 1:
			self.stream(stringList[0], stream)

		elif len(stringList) > 1:
			for string in stringList:
				count += 1
				b = self.changeVoice(string)

				#downloads the file with an extension of its count
				#appends the files in order in fileList
				self.stream(b, stream)

		#stop stream
		stream.stop_stream()
		stream.close()

		#closes pyaudio
		p.terminate()





#for more: http://docs.python-requests.org/en/master/user/quickstart/
