import pypyodbc
import json
import os

class Transcript():

    ### CONSTANTS ###

    STATUS_PENDING = 1
    STATUS_COMPLETE = 2
    STATUS_ERROR = 3

    WAV_FORM = "audio/wav"
    OGG_FORM = "audio/ogg;codecs=opus"

    ### CONSTRUCTOR ###

    def __init__(self, dataList):

        #extracting json data using json module and edits the information
        #loads the information into the members, to be put into two variables
        jsonItem = json.loads(dataList[4])
        filetype = (jsonItem["fileType"])
        voice = (jsonItem["voiceID"])

        #saves the information in the object
        self.identity = dataList[0]
        self.voiceTranscript = dataList[1]
        self.filename = dataList[2]
        self.filepath = dataList[3]
        self.fileType = filetype
        self.voiceID = voice
        self.status = STATUS_PENDING
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
    def getFilePath(self):
        return self.filepath

    def getFileName(self):
        return self.filename

    #method to get fileType
    #reformats fileType to fit necessities of watson api
    def getAccept(self):
        #adjusts the accept variable based on response
        if self.fileType == 'wav':
            accept = WAV_FORM
        elif self.fileType == 'ogg':
            accept = OGG_FORM
        elif self.fileType == 'vox':
            accept = WAV_FORM

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
            Logger.warning("No text input")
            self.status = self.STATUS_ERROR
            self.errorCode = -1
            return False
        else:
            return True

    #method to check validity of filename
    def checkFilename(self):
        for c in self.filename:
            if c == ':' or c == '.':
                self.status = self.STATUS_ERROR
                self.errorCode = -2
                return False

        return True

    #method to check validity of format type
    def checkFormat(self):
        #checks for 3 valid filetypes
        if (self.fileType != 'ogg' and self.fileType != 'wav' and self.fileType != 'vox'):
            self.status = self.STATUS_ERROR
            self.errorCode = -3
            return False
        else:
            return True

    #method to check validity of filepath
    def checkFilePath(self):
        #checks that path exists
        if not os.path.isdir(self.filepath):
            self.status = self.STATUS_ERROR
            self.errorCode = -4
            return False
        else:
            return True

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

        #creating a connection object through the pypyodbc module
        conn = pypyodbc.connect(constr)
        #cursor object for making changes or calling stored procedures
        crsr = conn.cursor()
        exStr = "UpdateTextToSpeechStaging %s, %s, %s" % (self.identity,
                                                          self.status,
                                                          self.errorCode)

        #executes stored procedure to update staging
        crsr.execute(exStr)
