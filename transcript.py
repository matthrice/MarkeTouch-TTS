import pyodbc
import json
import os



class Transcript():

    ### CONSTANTS ###

    STATUS_PENDING = 1
    STATUS_COMPLETE = 2
    STATUS_ERROR = 3

    WAV_FORM = "audio/wav"
    OGG_FORM = "audio/ogg;codecs=opus"

    #Error codes
    ERR_TRANSCRIPT_TEXT = -1    #invalid text to be synthsized
    ERR_FILENAME = -2           #invalid filename
    ERR_AUDIO_FORMAT = -3       #invalid audio format type
    ERR_FILEPATH = -4           #invalid filepath

    ### CONSTRUCTOR ###

    def __init__(self, dataList):

        #extracting json data using json module and edits the information
        #loads the information into the members, to be put into two variables
        jsonItem = json.loads(dataList[5])
        filetype = (jsonItem["fileType"])
        voice = (jsonItem["voiceID"])

        #saves the information in the object
        self.identity = dataList[0]
        self.voiceTranscript = dataList[1]
        self.filename = dataList[2]
        self.vox_filepath = dataList[3]
        self.wav_filepath = dataList[4]
        self.fileType = filetype
        self.voiceID = voice
        self.status = self.STATUS_PENDING
        self.errorCode = 0 #Null error on initialization


    ### GETTER FUNCTIONS ###

    #method to get identity
    def getIdentity(self):
        return self.identity

    #method to get status and errorCode
    def getStatus(self):
        return self.status

    #method to get errorCode
    def getError(self):
        return self.errorCode

    #method to get voiceID from member variables
    def getVoice(self):
        return self.voiceID

    #method to get transcript
    def getTranscriptText(self):
        return self.voiceTranscript

    #method to get filepath
    def getVoxFilePath(self):
        return self.vox_filepath

    #method to get wav filepath
    def getWavFilePath(self):
        return self.wav_filepath

    def getFileName(self):
        return self.filename

    #method to get fileType
    #reformats fileType to fit necessities of watson api
    def getAccept(self):
        #adjusts the accept variable based on response
        if self.fileType == 'wav':
            accept = self.WAV_FORM
        elif self.fileType == 'ogg':
            accept = self.OGG_FORM
        elif self.fileType == 'vox':
            accept = self.WAV_FORM

        return accept

    def getVoxBool(self):
        if self.fileType == 'vox':
            return True
        else:
            return False

    ### MEMBER FUNCTIONS ###

    #method to check a text phrase to synthesize voice
    def checkPhrase(self):
        #checks for empty input
        if self.voiceTranscript == '':
            self.status = self.STATUS_ERROR
            self.errorCode = self.ERR_TRANSCRIPT_TEXT
            return False
        else:
            return True

    #method to check validity of filename
    def checkFilename(self):
        for c in self.filename:
            if c == ':' or c == '.':
                self.status = self.STATUS_ERROR
                self.errorCode = self.ERR_FILENAME
                return False

        return True

    #method to check validity of format type
    def checkFormat(self):
        #checks for 3 valid filetypes
        if (self.fileType != 'ogg' and self.fileType != 'wav' and self.fileType != 'vox'):
            self.status = self.STATUS_ERROR
            self.errorCode = self.ERR_AUDIO_FORMAT
            return False
        else:
            return True

    #method to check validity of filepath
    def checkVoxFilePath(self):
        #checks that path exists
        if not os.path.isdir(self.vox_filepath):
            self.status = self.STATUS_ERROR
            self.errorCode = self.ERR_FILEPATH
            return False
        else:
            return True

    def checkWavFilePath(self):
        if not os.path.isdir(self.vox_filepath):
            self.status = self.STATUS_ERROR
            self.errorCode = self.ERR_FILEPATH
            return False
        else:
            return True

    def setStatus(self, newStatus):
        self.status = newStatus

    def setError(self, newError):
        self.errorCode = newError

    #method to update server information with the status of completion
    #if the process is pending, status = 1, errorCode = NULL
    #if the process is complete, status = 2, errorCode = NULL
    #if the process failed, status = 3, errorCode = some specfic error code
    def updateTranscriptData(self, DB_DRIVER, DB_HOST, DB_USER, DB_PASSWORD, DB_NAME):

        #string to connect to the server
        constr = "DRIVER=%s;SERVER=%s;UID=%s;PWD=%s;DATABASE=%s" % (DB_DRIVER,
                                                                    DB_HOST,
                                                                    DB_USER,
                                                                    DB_PASSWORD,
                                                                    DB_NAME)

        #creating a connection object through the pyodbc module
        conn = pyodbc.connect(constr)
        #cursor object for making changes or calling stored procedures
        crsr = conn.cursor()
        params = (self.identity, self.status, self.errorCode)
        exStr = "UpdateTextToSpeechStaging %s, %s, %s" % params
        #executes stored procedure to update staging
        crsr.execute(exStr)
        crsr.commit()

        conn.close()
