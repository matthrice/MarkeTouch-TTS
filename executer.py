import subprocess


#using wine because developing on a mac
#remove when running on windows
subprocess.call(r'copyfiles\vcecopy.exe wavfiles\piano2.wav wavfiles\piano2.vox', shell=True)
