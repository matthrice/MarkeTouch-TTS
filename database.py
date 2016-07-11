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
def checkPhrase(Logger, phrase):
    #checks for empty input
    if phrase == '':
        Logger.warning("No text input")
        return False

    if len(phrase) < 2:
        Logger.warning("Not enough text to synthesize")
        return False

    return True


#method to receive format of audio from user
#also recieves if the file is to be converted into vox
#returns a dictionary, in the format of (accept, voxBool)
def getFormat(Logger, formatType):
    assert(formatType != 'ogg' or formatType != 'wav' or formatType != 'vox')
    #adjusts the accept variable based on response
    if formatType = 'wav':
        accept = "audio/wav"
        Logger.info("File type: .wav")
        voxBool = False
    elif formatType = 'ogg':
        accept = "audio/ogg;codecs=opus"
        Logger.info("File type: .ogg")
        voxBool = False
    elif formatType = 'vox':
        accept = "audio/wav"
        Logger.info("File type: .vox")
        voxBool = True

    return {'accept':accept, 'voxBool':voxBool}

#method to receive filename from user
def checkFilename(Logger, filename):
    #filename and location input
    if not validFilename(filename):
        Logger.warning("Invalid input for filename: %s" % filename)
        return False

    #logs filename
    Logger.info("Filename: %s" % filename)

    return True

#method to receive filepath from user
def checkPath(Logger, location):
    #asserts that the path exists
    if not os.path.isdir(location):
        Logger.warning("Directory in path does not exist: %s" % location)
        return False

    return True

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
    dbList = (crsr.fetchall())

    #list looks like this currently:
    #identity, transcript, filename, filepath, json object (filetype and voiceID),

    conn.close()


    return dbList

def editTranscriptData(dbList_1):

    jsonItem = json.loads(dbList_1[4])
    fileType = (jsonItem["fileType"])
    voiceID = (jsonItem["voiceID"])

    dict1 = {'identity': dbList_1[0], 'voiceTranscript': dbList_1[1], 'filename': dbList_1[2],
            'filepath': dbList_1[3], 'fileType': fileType, 'voiceID': voiceID}

    return dict1

def audioConvert(text, filename, filepath, fileType, voiceID):
    # simple logger to act as parameter for the functions
    logging.basicConfig(filename='maintest.log', level=30)
    Logger = logging.getLogger("main_test_log")

    #disable warnings for requests library
    requests.packages.urllib3.disable_warnings()

    #checks valid text
    assert(checkPhrase(Logger, text))

    #audio format input
    #returns a short dictionary
    audioFormat = getFormat(Logger, audiofmt)

    #filename and location input
    assert(checkFilename(Logger, filename)
    assert(checkPath(Logger, filepath)

    #creates watson object
    watson = Watson(USERNAME, PASSWORD, voiceID,
                    URL, CHUNK_SIZE, audioFormat['accept'])

    fileList = watson.writeFiles(text, filename, filepath)
    if audioFormat['voxBool']:
        fullConvert(fileList)
        Logger.info("Vox filed created.")
    Logger.info("Request ID: 375832948 (placeholder)")

    print("Audio file saved.")

    Logger.info("Download successful.")

    #Indicates end of logging session, adds space between sessions
    Logger.info("* File session ended *\n\n")


dataSet = getTranscriptData()
for data in dataSet:
    newDict = editTranscriptData(data)
    audioConvert(newDict["voiceTranscript"], newDict["filename"], newDict["filepath"],
                 newDict["fileType"], newDict["voiceID"])
