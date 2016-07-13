import os
import datetime
import subprocess
import logging

import requests
import json
import pypyodbc

from logging.handlers import RotatingFileHandler
from watson import Watson

#GLOBALS#

#parameters for authorization and audio format
URL = 'https://stream.watsonplatform.net/text-to-speech/api'
PASSWORD = 'QiVBWYF2uBlJ'
USERNAME = 'be745e3d-8ee2-47b6-806a-cee0ac2a6683'
CHUNK_SIZE = 1024
WAV_FORM = "audio/wav"
OGG_FORM = "audio/ogg;codecs=opus"

#Information for logger
MEGABYTE = 1000000 #number of bytes in a megabyte
NOW = datetime.datetime.now()   #current time
LOG_FILE = "maintest.log"
LOG_OBJECT = "main_test_log"

#Server Information
DB_DRIVER = "{SQL Server}"
DB_HOST = "vbserv.archtelecom.com"
DB_NAME = "bcastdb"
DB_USER = "inetlog"
DB_PASSWORD = "evita"


#method for making a rotating log
#requires path is valid
#modifies log based on byte size and period of time
#creates multiple logs, as well as deleting them after 30 days
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
    if formatType == 'wav':
        accept = WAV_FORM
        Logger.info("File type: .wav")
        voxBool = False
    elif formatType == 'ogg':
        accept = OGG_FORM
        Logger.info("File type: .ogg")
        voxBool = False
    elif formatType == 'vox':
        accept = WAV_FORM
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
    #used specifically because it ignores bad header information (Watson .wav)
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
            print(fullPath)
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


#method for getting transcript data from the SERVER
#Server parameters and certification defined globally
#returns a list of lists, with the inner lists containing all the info for the
#specific text to speech staging
def getTranscriptData():

    #string to connect to the server
    connect_string1 = "DRIVER=%s;SERVER=%s;UID=%s;PWD=%s;DATABASE=%s" % (DB_DRIVER,
                                                                         DB_HOST,
                                                                         DB_USER,
                                                                         DB_PASSWORD,
                                                                         DB_NAME)

    #creating a connection object through the pypyodbc module
    #object that defines server relationship
    conn = pypyodbc.connect(connect_string1)

    #cursor object for making changes or calling stored procedures
    crsr = conn.cursor()
    #calling a stored procedure
    #"GetTextToSpeechStaging" is a function that retrieves all the information
    #for a transcript, shown below
    crsr.execute("GetTextToSpeechStaging")
    #fetchall() retrieves all data in one execution
    #thus limiting the amount of times the stored procedure must be called to once
    dbList = (crsr.fetchall())

    #list looks like this currently:
    #identity, transcript, filename, filepath, json object (filetype and voiceID),

    conn.close()

    #returns database list
    return dbList

def updateTranscriptData(requestID, status, errorCode):

    #string to connect to the server
    connect_string1 = "DRIVER=%s;SERVER=%s;UID=%s;PWD=%s;DATABASE=%s" % (DB_DRIVER,
                                                                         DB_HOST,
                                                                         DB_USER,
                                                                         DB_PASSWORD,
                                                                         DB_NAME)

    #creating a connection object through the pypyodbc module
    conn = pypyodbc.connect(connect_string1)
    #cursor object for making changes or calling stored procedures
    crsr = conn.cursor()
    exStr = "UpdateTextToSpeechStaging %s, %s, %s" % (requestID, status, errorCode)
    print(exStr)
    #crsr.execute(exStr)


#method to edit the data from the database to make it more usable
#takes a single list from the list of lists and reformats it into a dictionary
#does not take the full list of list from the server, this function must be used
#in a for loop if fetchall() is called
def editData(dbList_1):

    #extracting json data using json module
    #loads the information into a dictionary, to be put into two variables
    jsonItem = json.loads(dbList_1[4])
    fileType = (jsonItem["fileType"])
    voiceID = (jsonItem["voiceID"])

    #creates a six part dictionary defining each necessity of the TTS staging
    dict1 = {'identity': dbList_1[0], 'voiceTranscript': dbList_1[1],
             'filename': dbList_1[2], 'filepath': dbList_1[3],
             'fileType': fileType, 'voiceID': voiceID}

    return dict1


def audioConvert(requestID, text, filename, filepath, fileType, voiceID):
    #simple logger to act as parameter for the functions
    createRotatingLog(LOG_FILE)
    Logger = logging.getLogger(LOG_OBJECT)

    #disable warnings for requests library
    requests.packages.urllib3.disable_warnings()

    #checks valid text
    assert(checkPhrase(Logger, text))

    #audio format input
    #returns a short dictionary
    audioFormat = getFormat(Logger, fileType)

    #filename and location input
    assert(checkFilename(Logger, filename))
    assert(checkPath(Logger, filepath))

    #creates watson object
    watson = Watson(USERNAME, PASSWORD, voiceID,
                    URL, CHUNK_SIZE, audioFormat['accept'])


    fileList = watson.writeFiles(text, filename, filepath)
    if audioFormat['voxBool']:
        fullConvert(fileList)
        Logger.info("Vox filed created.")
    Logger.info("Request ID: %s" % requestID)

    print("Audio file saved.")

    Logger.info("Download successful.")

    #Indicates end of logging session, adds space between sessions
    Logger.info("* File session ended *\n\n")

def main():
    dataSet = getTranscriptData()
    for data in dataSet:
        newDict = editData(data)
        audioConvert(newDict["identity"], newDict["voiceTranscript"],
                     newDict["filename"], newDict["filepath"],
                     newDict["fileType"], newDict["voiceID"])


#runs main function
#if __name__ == "__main__":
    #main()

updateTranscriptData(1, 2, 3)
