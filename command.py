#File used for passing all parameters of text to speech script in the command line

#Arguments in order of appearance on the command line:
#1: User input of text to be synthesized
#2: Voice ID, male or female (1 = male, 0 = female)
#3: Stream or Download (1 = stream, 0 = download)
#   (At this point, if stream is chosen, there are no more args)
#4: Audio format, 1 = wav, 2 = ogg, 3 = vox
#5: filename, no extension used
#6: filepath, simple name and path of directory

#Example command line statement:

# This command would stream the word 'hello' in english with a female voice
#        $ python3 command.py "*English hello" 0 1

# This command downloads a vox file that says 'how are you' in english with a
# male voice, saved as voxfiles/example.vox
#        $ python3 command.py "*English how are you" 1 0 3 "example" "voxfiles"


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
import sys

argList = sys.argv

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
    if string == '0':
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
def getPhrase(Logger, phrase):
    #checks for empty input
    if phrase == '':
        Logger.warning("No text input")

    if len(phrase) < 2:
        Logger.warning("Not enough text to synthesize")

    return phrase

#method to request a voiceID yes or no answer
def getVoiceID(Logger, voiceIDBool):
    if not validBool(voiceIDBool):
        Logger.warning("Invalid input for VoiceID: %s" % voiceIDBool)

    if yesOrNo(voiceIDBool):
        voiceID = 'en-US_MichaelVoice'
    else:
        voiceID = 'en-US_AllisonVoice'

    return voiceID

#method to check if user wants to stream or download
#returns true or false
def isStream(Logger, streamBool):
    #stream input (determines whether code runs stream() or download())
    if not validBool(streamBool):
        Logger.warning("Invalid input for streamBool: %s" % streamBool)

    if yesOrNo(streamBool):

        return True
    else:
        return False

#method to receive format of audio from user
#also recieves if the file is to be converted into vox
#returns a dictionary, in the format of (accept, voxBool)
def getFormat(Logger, formatBool):
    fInt = int(formatBool)
    if fInt != 1 or fInt != 2 or fInt != 3:
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
        accept = "audio/ogg;codecs=opus"
        Logger.info("File type: .ogg")
        voxBool = True

    return {'accept':accept, 'voxBool':voxBool}

#method to receive filename from user
def getFilename(Logger, filename):
    #filename and location input
    if not validFilename(filename):
        Logger.warning("Invalid input for filename: %s" % filename)

    #logs filename
    Logger.info("Filename: %s" % filename)

    return filename

#method to receive filepath from user
def getPath(Logger, location):
    #asserts that the path exists
    if not os.path.isdir(location):
        Logger.warning("Directory in path does not exist: %s" % location)

    return location

#method to initially convert ogg file to wav
def convertToWav(filename):
    #strips ogg extension and attaches .wav
    wavName = filename[:-4] + '.wav'
    #creates command line for ffmpeg
    command = ["ffmpeg", "-i", filename, wavName]
    #ffmpeg is a service for command line conversion
    #used specifically because it ignores bad header information (Watson wav files)
    #called through subprocess to return converted file
    subprocess.call(command, shell=True)

    #removes ogg file
    os.remove(filename)

    #returns string name reference to the wavfile
    return wavName

#method to convert a wav file to a vox file, provided full path
def convertToVox(filename, voxName):
    #creates command for vcecopy, another command line executable
    #vcecopy handles wav -> vox conversion
    command = [r"copyfiles\vcecopy", filename, voxName]
    subprocess.call(command, shell=True)

    #removes wav file
    os.remove(filename)

#method to convert ogg file to vox
#ties together methods above to create a single command conversion
def fullConvert(stringList):
    #with only one element in the list, conversion is simple
    #extract filename, end with vox, convert
    if len(stringList) == 1:
        #takes first and only element from the list
        for string in stringList:
            filepath = string[0]
            filename = string[1]
            fullPath = filepath + '\\' + filename + '.ogg'
            #wavPath is the filepath to the newly converted file, ogg->wav
            wavPath = convertToWav(fullPath)
            #voxName is the new file for conversion, removes '.wav'
            #and replaces it with '.vox', so the file will still have the user's
            #desired name choice
            voxPath = fullPath[:-4] + '.vox'

            #end conversion of wav->vox
            convertToVox(wavPath, voxPath)

    #else clause for the event of merging multiple files
    else:

        for string in stringList:
            filepath = string[0]
            filename = string[1]

            fullPath = filepath + '\\' + filename + '.ogg'
            wavPath = convertToWav(fullPath)

            #removes the .ogg extension as well as the numeric identifier
            #that organizes the ogg/wav files.
            #each file will be subsequently converted to the same vox name
            #merging the files in the process
            voxPath = fullPath[:-5] + '.vox'
            convertToVox(wavPath, voxPath)


def main():
    argv = sys.argv

    #creates the log session
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
    #phrase input
    userInput = getPhrase(Logger, argv[1])
    #breaks loop
    #voiceID input (bool conversion to string)
    voiceID = getVoiceID(Logger, argv[2])

    if isStream(Logger, argv[3]):
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
        #returns a short dictionary
        audioFormat = getFormat(Logger, argv[4])
        #filename and location input
        filename = getFilename(Logger, argv[5])
        location = getPath(Logger, argv[6])

        #creates watson object
        watson = Watson(USERNAME, PASSWORD, voiceID,
                        URL, CHUNK_SIZE, audioFormat['accept'])
        #writes files
        fileList = watson.writeFiles(userInput, filename, location)
        if audioFormat['voxBool']:
            fullConvert(fileList)
            Logger.info("Vox filed created.")
        Logger.info("Request ID: 375832948 (placeholder)")

        print("Audio file saved.")

        Logger.info("Download successful.")

    #Indicates end of logging session, adds space between sessions
    Logger.info("* File session ended *\n\n")

#runs main function
if __name__ == "__main__":
    main()
