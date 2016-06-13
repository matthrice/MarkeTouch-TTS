import logging
import time
from logging.handlers import RotatingFileHandler
from watson import Watson
import requests
import pyaudio
import wave
import os
import datetime
import subprocess

#parameters for authorization and audio format
URL = 'https://stream.watsonplatform.net/text-to-speech/api'
PASSWORD = 'QiVBWYF2uBlJ'
USERNAME = 'be745e3d-8ee2-47b6-806a-cee0ac2a6683'
CHUNK_SIZE = 1024
#Information for logger
MEGABYTE = 1000000 #number of bytes in a megabyte
now = datetime.datetime.now()   #current time


#method for making a rotating log
#REQUIRES: Path is valid
#MODIFIES: Log based on byte size and period of time
#EFFECTS: Creates multiple logs, as well as deleting them after 30 days
def createRotatingLog(path):
    #initiates logging session
    Logger = logging.getLogger("TTS")
    Logger.setLevel(logging.DEBUG)
    #defines handler for byte size
    #will roll over after 100 mb, will max out at 10 backup files
    sizeHandler = RotatingFileHandler(path, maxBytes=(MEGABYTE * 100),
                                  backupCount=10)
    fmtr = logging.Formatter('%(asctime)s %(levelname)s %(message)s',
                             datefmt='%H:%M:%S')

    sizeHandler.setFormatter(fmtr)
    sizeHandler.setLevel(logging.DEBUG)

    Logger.addHandler(sizeHandler)

    return Logger


#Bool method to assert whether the string is intended to return
#True or False
def yesOrNo(string):
    if string == '1':
        return True
    else:
        return False


#Bool method that shows the input is valid (a 1 or a 0)
def validBool(string):
    if string == '1' or string == '0':
        return True
    else:
        return False


#Bool method that shows the filename does not contain bad characters
def validFilename(string):
    for c in string:
        if c == ':' or c == '.':
            return False

    return True

#method to request a text phrase to synthesize voice
def requestPhrase(Logger):
    userInput = input("Enter a phrase: ")
    #checks for empty input
    if userInput == '':
        Logger.warning("No text input")

    if len(userInput) < 2:
        Logger.warning("Not enough text to synthesize")

    return userInput

#method to request a voiceID yes or no answer
def requestVoiceID(Logger):
    voiceIDBool = input("Enter 1 to hear male voice, 0 to hear female voice: ")
    if not validBool(voiceIDBool):
        Logger.warning("Invalid input for VoiceID: %s" % voiceIDBool)

    if yesOrNo(voiceIDBool):
        voiceID = 'en-US_MichaelVoice'
    else:
        voiceID = 'en-US_AllisonVoice'

    return voiceID

#method to check if user wants to stream or download
#returns true or false
def isStream(Logger):
    #stream input (determines whether code runs stream() or download())
    streamBool = input("Enter 1 to stream, enter 0 to download: ")
    if not validBool(streamBool):
        Logger.warning("Invalid input for streamBool: %s" % streamBool)

    if yesOrNo(streamBool):

        return True
    else:
        return False

#method to receive format of audio from user
#also recieves if the file is to be converted into vox
#returns a dictionary, in the format of (accept, voxBool)
def requestFormat(Logger):
    formatBool = input("Enter 1 for .wav, enter 2 for .ogg, enter 3 for .vox: ")
    fInt = int(formatBool)
    if fINt != 1 or fInt != 2 or fInt != 3:
        Logger.warning("Invalid input for formatBool: %s" % formatBool)

    #adjusts the accept variable based on response
    if fInt == 1:
        accept = "audio/wav"
        Logger.info("File type: .wav")
        voxBool = False
    elif fInt == 2:
        accept = "audio/ogg;codecs=opus"
        Logger.info("File type: .ogg")
        voxBool = False
    elif fInt == 3:
        accept = "audio/wav"
        Logger.info("File type: .vox")
        voxBool = True

    return {'accept':accept, 'voxBool':voxBool}

#method to receive filename from user
def requestFilename(Logger):
    #filename and location input
    filename = input("Enter a name for the file: ")
    if not validFilename(filename):
        Logger.warning("Invalid input for filename: %s" % filename)

    #logs filename
    Logger.info("Filename: %s" % filename)

    return filename

#method to receive filepath from user
def requestPath(Logger):
    location = input("Enter a location for the file: ")
    #asserts that the path exists
    if not os.path.isdir(location):
        Logger.warning("Directory in path does not exist: %s" % location)

    return location

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
            voxName = filename[:-3] + 'vox'
            print(voxName)
            fullPath = filepath + '\\' + filename
            voxPath = filepath + '\\' + voxName
            command = r"copyfiles\vcecopy.exe " + fullPath + " " + voxPath
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
            voxName = filename[:-5] + '.vox'
            fullPath = filepath + '\\' + filename
            voxPath = filepath + '\\' + voxName
            command = r"copyfiles\vcecopy.exe " + fullPath + " " + voxPath
            #from here the process is the same
            #vcecopy will append each file to the same voxName file
            #thus it will merge all wav files to one vox file
            subprocess.call(command, shell=True)
            Logger.info("Files merged in vox conversion.")
            #each time, old .wav files are removed, leaving one vox file
            #os.remove(string)

def main():

    Logger = createRotatingLog("TTS.log")
    Logger.info("* File session started *")


    #disable warnings for requests library
    requests.packages.urllib3.disable_warnings()

    #empty variables to be used as parameters for download()
    userInput = ''
    filename = ''
    location = ''
    accept = 'audio/wav'
    voiceID = ''

    #main function, loops until user types quit
    while userInput != 'quit':
        #phrase input
        userInput = requestPhrase(Logger)
        #breaks loop
        if userInput != 'quit':
            #voiceID input (bool conversion to string)
            voiceID = requestVoiceID(Logger)

            if isStream(Logger):
                Logger.info("Output: Stream.")
                #creates watson object, wav is default for stream
                watson = Watson(USERNAME, PASSWORD, voiceID,
                                URL, CHUNK_SIZE, 'audio/wav')
                watson.playFiles(userInput)

                #Request ID placeholder
                Logger.info("Request ID: 375832948 (placeholder)")
                Logger.info("Stream successful.")
            else:
                #audio format input
                audioFormat = requestFormat(Logger)
                #filename and location input
                filename = requestFilename(Logger)
                location = requestPath(Logger)

                #creates watson object
                watson = Watson(USERNAME, PASSWORD, voiceID,
                                URL, CHUNK_SIZE, audioFormat['accept'])
                #writes files
                fileList = watson.writeFiles(userInput, filename, location)
                if audioFormat['voxBool']:
                    convertToVox(fileList)
                    Logger.info("Vox filed created.")
                Logger.info("Request ID: 375832948 (placeholder)")

                print("Audio file saved.")

                Logger.info("Download successful.")

    #Indicates end of logging session, adds space between sessions
    Logger.info("* File session ended *\n\n")

#runs main function
if __name__ == "__main__":
    main()
