import subprocess


fileList = ["piano2.wav"]

#using wine because developing on a mac
#remove when running on windows
subprocess.call(['wine vcecopy.exe'] + fileList, shell=True)
