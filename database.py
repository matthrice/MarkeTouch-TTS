import pypyodbc
import json
import logging
from logging.handlers import RotatingFileHandler
from watson import Watson
import requests
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
        accept = "audio/wav"
        Logger.info("File type: .vox")
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
    wavName = filename[:-4] + '2.wav'
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
    voxName = voxName[:-5] + ".vox"
    #creates command for vcecopy, another command line executable
    #vcecopy handles wav -> vox conversion
    command = [r"copyfiles\vcecopy", "-m", ",1", "-c4", filename, voxName]
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
            fullPath = filepath + '\\' + filename + '.wav'
            #wavPath is the filepath to the newly converted file, ogg->wav
            wavPath = convertToWav(fullPath)
            #voxName is the new file for conversion, removes '.wav'
            #and replaces it with '.vox', so the file will still have the user's
            #desired name choice
            voxPath = wavPath[:-4] + '.vox'

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



def getTranscriptData():

    dbDriver = "{SQL Server}"
    dbHost = "vbserv.archtelecom.com"
    dbName = "bcastdb"
    dbUser = "inetlog"
    dbPassword = "evita"

    connect_string1 = "DRIVER=%s;SERVER=%s;UID=%s;PWD=%s;DATABASE=%s" % (dbDriver, dbHost, dbUser, dbPassword, dbName)
    conn = pypyodbc.connect(connect_string1)

    crsr = conn.cursor()
    crsr.execute("GetTextToSpeechStaging")

    dbList = (crsr.fetchmany(1))[0]


    jsonItem = json.loads(dbList[4])
    fileType = (jsonItem["fileType"])
    voiceID = (jsonItem["voiceID"])

    dict = {'identity': dbList[0], 'voiceTranscript': dbList[1], 'number': dbList[2],
            'filePath': dbList[3], 'fileType': fileType, 'voiceID': voiceID}

    conn.close()


    return dict

def createArguments(dict):
    transcript = "*English " + dict["voiceTranscript"]
    filepath = dict["filePath"]

    if dict["fileType"] == "wav":
        audioFormat = 1
    elif dict["fileType"] == "ogg":
        audioFormat = 2
    elif dict["fileType"] == "vox":
        audioFormat = 3

    if dict["voiceID"] == "en-US_AllisonVoice":
        voiceID = 0
    elif dict["voiceID"] == "en-US_MichaelVoice":
        voiceID = 1

    return transcript, filepath, audioFormat, voiceID


def tempConverter(text, voice, downloadBool, audiofmt, fileN, fileP):
    # simple logger to act as parameter for the functions
    logging.basicConfig(filename='maintest.log', level=30)
    Logger = logging.getLogger("main_test_log")

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
    userInput = getPhrase(Logger, text)
    #breaks loop
    #voiceID input (bool conversion to string)
    voiceID = getVoiceID(Logger, voice)

    if isStream(Logger, downloadBool):
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
        audioFormat = getFormat(Logger, audiofmt)
        print(audioFormat)
        #filename and location input
        filename = getFilename(Logger, fileN)
        location = getPath(Logger, fileP)

        #creates watson object
        watson = Watson(USERNAME, PASSWORD, voiceID,
                        URL, CHUNK_SIZE, audioFormat['accept'])
        #writes files
        print(voiceID, downloadBool, audioFormat, filename, location)
        fileList = watson.writeFiles(userInput, filename, location)
        if audioFormat['voxBool']:
            fullConvert(fileList)
            Logger.info("Vox filed created.")
        Logger.info("Request ID: 375832948 (placeholder)")

        print("Audio file saved.")

        Logger.info("Download successful.")

    #Indicates end of logging session, adds space between sessions
    Logger.info("* File session ended *\n\n")


firstSet = getTranscriptData()
transcript, filepath, audioFormat, voiceID = createArguments(firstSet)

tempConverter(transcript, voiceID, 0, audioFormat, "hereitgoes", "wavfiles")