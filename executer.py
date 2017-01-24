import subprocess
import requests
import os
import wave

URL = 'WATSON_URL'
PASSWORD = 'WATSON_PASSWORD'
USERNAME = 'WATSON_USERNAME'
CHUNK_SIZE = 1024

def download(text, filename, path):
		#requests gets response using parameters for authorization and audio format
		#stream=True allows it to be streamed as well
		#verify=False ignores SSL certification
		r = requests.get(URL + "/v1/synthesize",
                           auth=(USERNAME, PASSWORD),
                           params={'text': text, 'voice': 'en-US_AllisonVoice', 'accept': 'audio/ogg;codecs=opus'},
                           verify=False
                           )
		#ensures path and directory exist
		if not os.path.exists(path):
			os.makedirs(path)

		#opens filename from stream and saves it into filename
		#'wb' indicates file is opened for writing in binary mode
		#joins path and filename
		with open(os.path.join(path, filename + '.ogg'), 'wb') as fd:
			for chunk in r.iter_content(CHUNK_SIZE):
				fd.write(chunk)

		listElement = [path, filename]
		return listElement

	#reads in input and determines if more than one file is needed to download
	#REQUIRES: Text is in format of *LANGUAGE text
	#EFFECTS: Produces a single file if no language change, or produces several
	#files with a number extension marking their order if text uses multiple
	#languages

def writeFiles(text, filename, path):
	print("\nConverting text.\n")

	#saves english voice specification
	english = 'en-US_AllisonVoice'
	#creates a counter for the filenames
	count = 0
	#creates an extension for the filename
	extension = ""

	#empty list for storing filenames
	#will be used later in main for conversion to vox
	fileList = []

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
			voice = "es-US_SofiaVoice"
			#checks if no language change, if so leaves off count
			if len(stringList) == 1:
				#downloads file, also appends to fileList
				f = download(b, filename + extension, path)
				fileList.append(f)
			else:
				f = download(b, filename + str(count)
							 + extension, path)
				fileList.append(f)
		#creates an english file
		elif a == "English":
			voice = english
			#checks if no language change, if so leaves off count
			if len(stringList) == 1:
				f = download(b, filename + extension, path)
				fileList.append(f)
			else:
				f = download(b, filename + str(count)
				                  + extension, path)
				fileList.append(f)

		#returns a list of all files written
		#returns them as a list of 2 element lists
		#each element contains both the filename and its path
		#useful later for vox conversion and merging
	return fileList

def setWAV(filename):
	wavfile = wave.open(filename, 'w') #opens a wave object for writing binary
	wavfile.setframerate(48000)
	wavfile.setnchannels(2)
	wavfile.setsampwidth(2)
	wavfile.close()

def getParams(filename):
	wavfile = wave.open(filename, 'r')
	print("num channels: %s" % wavfile.getnchannels())
	print("sample width: %s" % wavfile.getsampwidth())
	print("framerate: %s" % wavfile.getframerate())
	print("comptype: %s" % wavfile.getcomptype())
	print("compname: %s" % wavfile.getcompname())

	wavfile.close()

def convertToWav(filename):
	wavName = filename[:-4] + '.wav'
	command = ["ffmpeg", "-i", filename, wavName]
	subprocess.call(command, shell=True)

	return wavName

def convertToVox(filename, voxName):
	command = [r"copyfiles\vcecopy", filename, voxName]
	subprocess.call(command, shell=True)

#method to convert wav file to vox
def fullConvert(stringList):
	#with only one element in the list, conversion is simple
	#extract filename, end with vox, convert
	if len(stringList) == 1:
		#takes first and only element from the list
		for string in stringList:
			filepath = string[0]
			filename = string[1]
			#voxName is the new file for conversion, removes '.wav'
        	#and replaces it with '.vox', so the file will still have the user's
        	#desired name choice
			fullPath = filepath + '\\' + filename + '.ogg'
			wavPath = convertToWav(fullPath)
			voxPath = fullPath[:-4] + '.vox'
			convertToVox(wavPath, voxPath)

	else:

		for string in stringList:
			filepath = string[0]
			filename = string[1]
			filename = filename[:-1]

			fullPath = filepath + '\\' + filename + '.ogg'
			wavPath = convertToWav(fullPath)
			voxPath = fullPath[:-4] + '.vox'
			convertToVox(wavPath, voxPath)

			#the old .wav file is removed, leaving only the vox file
            #os.remove(string)

'''full test of executer'''
#strList = writeFiles("*English hi how are you", "middletest", "wavfiles") #writes a temporary wave file to convert
#fullConvert(strList)


'''simple test of watson-produced wave'''
#subprocess.call(r"<path to vcecopy exe> <path to wav> <path to vox>")

'''simple test of sample wave'''
#subprocess.call(r"<path to vcecopy exe> <path to wav> <path to vox>)

'''wave parameter testing'''
#getParams(r"path to wav")
#getParams(r"path to wav")
