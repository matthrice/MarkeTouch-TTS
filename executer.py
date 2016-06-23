import subprocess
import requests
import os
import wave

URL = 'https://stream.watsonplatform.net/text-to-speech/api'
PASSWORD = 'QiVBWYF2uBlJ'
USERNAME = 'be745e3d-8ee2-47b6-806a-cee0ac2a6683'
CHUNK_SIZE = 1024

def download(text, filename, path):
		#requests gets response using parameters for authorization and audio format
		#stream=True allows it to be streamed as well
		#verify=False ignores SSL certification
		r = requests.get(URL + "/v1/synthesize",
                           auth=(USERNAME, PASSWORD),
                           params={'text': text, 'voice': 'en-US_AllisonVoice', 'accept': 'audio/I16;rate=8000'},
                           verify=False
                           )
		#ensures path and directory exist
		if not os.path.exists(path):
			os.makedirs(path)

		#opens filename from stream and saves it into filename
		#'wb' indicates file is opened for writing in binary mode
		#joins path and filename
		with open(os.path.join(path, filename + '.vce'), 'wb') as fd:
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

#method to convert wav file to vox
def convertToVox(stringList):
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
            voxName = filename + '.vox'
            print(voxName)
            fullPath = filepath + '\\' + filename + '.vce'
            setWAV(fullPath)
            voxPath = r"%s\%s" % (filepath, voxName)
            command = [r"copyfiles\vcecopy.exe", fullPath,'-e', '16', voxPath]
            #uses subprocess module to call a line for the command line
            #command line executes a script which should appear along the lines:
            # $ vcecopy.exe example.wav example.vox
            subprocess.call(command, shell=True)
            #vcecopy is an executable which does the actual conversion

            #the old .wav file is removed, leaving only the vox file
            #os.remove(string)
    #if there are multiple files (language change) the conversion is different
    else:
        #cycles through files (each with a number on the end)
        for string in stringList:
            filepath = string[0]
            filename = string[1]
            #removes the number from the end of the files and '.wav'
            #adds '.vox' this time, because more characters are removed
            voxName = filename + '.vox'
            fullPath = filepath + '\\' + filename + '.vce'
            setWAV(fullPath)
            voxPath = r"%s\%s" % (filepath, voxName)
            command = r"copyfiles\vcecopy.exe " + fullPath + " " + voxPath + '-e16'
            #from here the process is the same
            #vcecopy will append each file to the same voxName file
            #thus it will merge all wav files to one vox file
            subprocess.call(command, shell=True)
            #each time, old .wav files are removed, leaving one vox file
            #os.remove(string)

'''full test of executer'''
strList = writeFiles("*English hi how are you", "test5", "wavfiles") #writes a temporary wave file to convert
convertToVox(strList)

'''simple test of watson-produced wave'''
#subprocess.call(r"copyfiles\vcecopy.exe wavfiles\hello.wav wavfiles\hello.vox")

'''simple test of sample wave'''
#subprocess.call(r"copyfiles\vcecopy.exe wavfiles\piano2.wav wavfiles\piano2.vox")

'''wave parameter testing'''
#getParams(r"wavfiles\test3.wav")
#getParams(r"wavfiles\piano2.wav")