import os
import datetime
import subprocess
import logging

#module for http requests
import requests
#module for parsing json
import json
#module for accessing SQL server
import pypyodbc

from logging.handlers import RotatingFileHandler
from watson import Watson
from transcript import Transcript

#GLOBALS#

#parameters for authorization and audio format
URL = 'https://stream.watsonplatform.net/text-to-speech/api'
PASSWORD = 'QiVBWYF2uBlJ'
USERNAME = 'be745e3d-8ee2-47b6-806a-cee0ac2a6683'

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
    elif not transcript.checkFilePath():
        Logger.warning("Directory in path does not exist: %s" % transcript.filepath)
        transcript.updateTranscriptData(DB_DRIVER, DB_HOST, DB_USER,
                                        DB_PASSWORD, DB_NAME)
        return False
    else:
        transcript.updateTranscriptData(DB_DRIVER, DB_HOST, DB_USER,
                                        DB_PASSWORD, DB_NAME)
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


def audioConvert(transcript):
    #simple logger to act as parameter for the functions
    createRotatingLog(LOG_FILE)
    Logger = logging.getLogger(LOG_OBJECT)

    #disable warnings for requests library
    requests.packages.urllib3.disable_warnings()


    #creates watson object
    watson = Watson(USERNAME, PASSWORD, URL, transcript)


    fileList = watson.writeFiles()
    if transcript.getVoxBool():
        fullConvert(fileList)
        Logger.info("Vox filed created.")
    Logger.info("Request ID: %s" % transcript.getIdentity())

    print("Audio file saved.")

    Logger.info("Download successful.")

    #Indicates end of logging session, adds space between sessions
    Logger.info("* File session ended *\n\n")

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

    #creating a connection object through the pypyodbc module
    #object that defines server relationship
    conn = pypyodbc.connect(constr)

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



def main():
    dataSet = getTranscriptData()
    for data in dataSet:
        transcript = Transcript(data)
        if checkTranscript(transcript):
            audioConvert(transcript)

#runs main function
if __name__ == "__main__":
    main()
