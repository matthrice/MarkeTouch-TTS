
#######        TEXT TO SPEECH         #####

### PYTHON SCRIPT TO SYNTHESIZE AUDIO FROM TEXT ###

#Receives the transcript data from database stored procedure
#Takes data and edits it for audio conversion
#Checks audio for errors, updates database status if so
#Synthesizes audio as a wav, ogg, or vox file
#Stores audio in desired location
#Logs activity in a file and records errors in database

## USER INPUT ERRORS ##

# -1 : Invalid text input, can't be synthesized
# -2 : Invalid filename
# -3 : Invalid audio format type
# -4 : Invalid filepath

## HTTP ERRORS ##

# 401 : Invalid username and password
# 404 : Invalid voice
# 406 : Invalid audio format

import os
import shutil
import datetime
import subprocess
import logging

#module for http requests
import requests
#module for accessing SQL server
import pyodbc

from logging.handlers import RotatingFileHandler
from watson import Watson
from transcript import Transcript



## GLOBALS ##

#parameters for authorization and audio format
W_URL = 'https://stream.watsonplatform.net/text-to-speech/api'
W_PASSWORD = 'QiVBWYF2uBlJ'
W_USERNAME = 'be745e3d-8ee2-47b6-806a-cee0ac2a6683'

#parameters for network authorization
N_DOMAIN = "nurl"
N_PASSWORD = "npassword"
N_USERNAME = 'nusername'

#Information for logger
MEGABYTE = 1000000 #number of bytes in a megabyte
NOW = datetime.datetime.now()   #current time
LOG_FILE = "info.txt"


#Server Information
DB_DRIVER = "{SQL Server}"
DB_HOST = "vbserv.archtelecom.com"
DB_NAME = "bcastdb"
DB_USER = "inetlog"
DB_PASSWORD = "evita"

VCECOPY_PATH = r"C:\Users\mattr\TTS-app\MarkeTouch-TTS\copyfiles\vcecopy"
FFMPEG_PATH = r"C:\Users\mattr\TTS-app\MarkeTouch-TTS\copyfiles\ffmpeg"
FINAL_PATH = r"\VSTORE1\ivrfiles\vbx\vmail\master.vox"


#method for making a rotating log
#requires path is valid
#modifies log based on byte size and period of time
#creates multiple logs, as well as deleting them after 30 days
def createRotatingLog(path, logObject):
    #initiates logging session
    Logger = logging.getLogger(logObject)
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

#method for general error handling
#checks the transcript data for errors
#if the method comes across an error, it updates both the logger and the
#database with an error code. Additionally, it immediately returns False
#So if the data is invalid, the transcript won't be converted
def checkTranscript(Logger, transcript):
    if not transcript.checkFilename():
        Logger.warning("Invalid input for filename: %s" % transcript.filename)
        transcript.updateTranscriptData(DB_DRIVER, DB_HOST, DB_USER,
                                        DB_PASSWORD, DB_NAME)
        return False
    elif not transcript.checkPhrase():
        Logger.warning("No text input")
        transcript.updateTranscriptData(DB_DRIVER, DB_HOST, DB_USER,
                                        DB_PASSWORD, DB_NAME)
        return False
    elif not transcript.checkFormat():
        Logger.warning("Invalid input for audio format: %s" % transcript.fileType)
        transcript.updateTranscriptData(DB_DRIVER, DB_HOST, DB_USER,
                                        DB_PASSWORD, DB_NAME)
        return False
    elif not transcript.checkVoxFilePath():
        Logger.warning("Directory in path does not exist: %s" % transcript.wav_filepath)
        transcript.updateTranscriptData(DB_DRIVER, DB_HOST, DB_USER,
                                        DB_PASSWORD, DB_NAME)
        return False
    elif not transcript.checkWavFilePath():
        Logger.warning("Directory in path does not exist: %s" % transcript.vox_filepath)
        transcript.updateTranscriptData(DB_DRIVER, DB_HOST, DB_USER,
                                        DB_PASSWORD, DB_NAME)
        return False
    else:
        transcript.updateTranscriptData(DB_DRIVER, DB_HOST, DB_USER,
                                        DB_PASSWORD, DB_NAME)
        return True

#method to initially convert ogg file to wav
#Uses ffmpeg
def convertToWav(filename):
    #strips ogg extension and attaches .wav
    wavName = filename[:-4] + '2.wav'
    #creates command line for ffmpeg
    command = [FFMPEG_PATH, "-i", filename, wavName]
    #ffmpeg is a service for command line conversion
    #used specifically because it ignores bad header information (Watson .wav)
    #called through subprocess to return converted file
    subprocess.call(command, shell=True)

    #removes ogg file
    os.remove(filename)

    #returns string name reference to the wavfile
    return wavName

#method to convert a wav file to a vox file, provided full path
#uses vcecopy
def convertToVox(filename, voxPath):
    voxName = filename[:-5] + ".vox"

    #creates command for vcecopy, another command line executable
    #vcecopy handles wav -> vox conversion
    command = [VCECOPY_PATH, "-m", ",1", "-c4", filename, voxName]
    subprocess.call(command, shell=True)

    #move the file from the wavfiles folder to the transcript's path
    shutil.move(voxName, voxPath)

    #removes wav file (vox file already removed)
    os.remove(filename)

#method to convert ogg file to vox
#ties together methods above to create a single command conversion
def fullConvert(stringList, voxPath):
    #with only one element in the list, conversion is simple
    #extract filename, end with vox, convert
    if len(stringList) == 1:
        #takes first and only element from the list
        for string in stringList:
            filepath = string[0]
            filename = string[1]
            if filepath == "Error":
                print("Unable to convert.")
                return filepath
            else:
                fullPath = filepath + '\\' + filename + '.wav'
                #wavPath is the filepath to the newly converted file, ogg->wav
                wavPath = convertToWav(fullPath)
                #voxName is the new file for conversion, removes '.wav'
                #and replaces it with '.vox', so the file will still have the user's
                #desired name choice
                voxPath = voxPath + filename + '.vox'
                print(voxPath)

                #end conversion of wav->vox
                convertToVox(wavPath, voxPath)

        return "None"

    #else clause for the event of merging multiple files
    else:

        for string in stringList:
            filepath = string[0]
            filename = string[1]

            if filepath == "Error":
                print("Unable to convert.")
                return filename
            else:
                fullPath = filepath + '\\' + filename + '.ogg'
                wavPath = convertToWav(fullPath)

                #removes the .ogg extension as well as the numeric identifier
                #that organizes the ogg/wav files.
                #each file will be subsequently converted to the same vox name
                #merging the files in the process
                voxPath = voxPath + filename + '.vox'
                convertToVox(wavPath, voxPath)

        return "None"

#Synthesizes the audio and carefully logs results
#takes in the transcript and creates a watson object, checks validity
#Only takes in one transcript at a time
def synthesize(Logger, transcript):

    #disable warnings for requests library
    requests.packages.urllib3.disable_warnings()

    print(transcript.getVoxFilePath())

    #creates watson object
    watson = Watson(W_USERNAME, W_PASSWORD, W_URL, transcript)
    Logger.info("Request ID: %s" % transcript.getIdentity())
    Logger.info("Filename: %s" % transcript.getFileName())
    Logger.info("Audio format: %s" % transcript.checkFormat())

    fileList = watson.writeFiles()
    if transcript.getVoxBool():
        error = fullConvert(fileList, transcript.getVoxFilePath())
    if error == "Error":
        Logger.info("Failure: %s" % transcript.getError())
        Logger.info("Unsuccessful download.")

    if error == "None":
        transcript.setStatus(transcript.STATUS_COMPLETE)
        Logger.info("Successful download.")


    #Indicates end of logging session, adds space between sessions
    Logger.info("\n\n")

#method to get the transcript data from the DATABASE
#requires credentials to the database, utilizes GetTextToSpeechStaging stored proc
#returns a list of lists, with the inner lists containing all the information
#for individual transcripts
def getTranscriptData():

    #string to connect to the server
    constr = "DRIVER=%s;SERVER=%s;UID=%s;PWD=%s;DATABASE=%s" % (DB_DRIVER,
                                                                DB_HOST,
                                                                DB_USER,
                                                                DB_PASSWORD,
                                                                DB_NAME)

    #creating a connection object through the pyodbc module
    #object that defines server relationship
    conn = pyodbc.connect(constr)

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

    return dbList

## MAIN ##

#Uses a for loop to cycle through the data received in getTranscriptData()
#In each cycle it creates a log and a transcript object
#checks the transcript, and if it passes, it synthesizes the text to audio
#Updates database with new information about the process
#returns nothing
def main():
    #creates a list of lists out of the database transcripts
    dataSet = getTranscriptData()
    #iterates through the lists
    for data in dataSet:
        #creates a transcript object out of each piece of data
        transcript = Transcript(data)
        Logger = createRotatingLog(LOG_FILE, str(transcript.getIdentity()))
        #ensures the data is valid
        if checkTranscript(Logger, transcript):
            #synthesizes transcript to audio
            synthesize(Logger, transcript)
            #transcript.updateTranscriptData(DB_DRIVER, DB_HOST, DB_USER,
                                            #DB_PASSWORD, DB_NAME)


#runs main function, more usable as a module
if __name__ == "__main__":
    main()
