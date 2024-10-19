#### Setup ####
###Imports###
import time
import threading
import subprocess
import ipaddress
import re

#### Function to turn cli output into an array, each line being an item in the array###
def getOutput(Command):
  temp = subprocess.Popen(Command, shell=True, stdout=subprocess.PIPE)
  output,error = temp.communicate()
  output = output.decode("utf-8")
  output = output.splitlines()
  return output

### Function to write errors to our error file ### LEAVE OUT THE BITS FOR RANDOM RETRYING FOR NOW AND WELL SEE HOW IT GOES
def errWrite(Message):
  with open("/home/PingMaker/errors/Errors.txt", "a") as errfile:
    errfile.write("\n"+Message)

#### Function to do a quick address format validation on the targets in the target file. X.X.X.X and XXX.XXX(sorta) for ips and hostnames###
def testTargetRegex(Target):
  regex = r"^((25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])\.){3}(25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])$"
  if re.search(regex, Target):
    return True
  else:
    regex = "[a-zA-Z0-9@:%._\\+~#?&//=]{2,256}\\.[a-z]" + "{2,6}\\b([-a-zA-Z0-9@:%._\\+~#?&//=]*)"
    if re.search(regex,Target):
      return True
    else:
      errWrite("Regex test failed for: " + Target)
      return False
  
### Function to get targets from target file. then parse through them and remove bad ones
def getTargets():
# Create empty list of targets, then go through the target file to find them
  ListOfTargets = []
  with open("/home/PingMaker/PingTargets.txt", "r") as targetFile:
    for line in targetFile:
      # If there is a /, it means there is a cidr address range. Get the addresses and add them all
      if "/" in line:
        usableSubnet = [str(ip) for ip in ipaddress.IPv4Network(line.replace("\n",""))]
        for ip in usableSubnet[1:-1]:
          ListOfTargets.append(str(ip))
      # Otherwise, if there is no /, it means it is either an IP or a hostname.
      else:
        ListOfTargets.append(line.replace("\n",""))
  #Now, run Regex checks on every target in order to have a quick validation. This will not grab all of the bad ones, but it will do most. Later, we will have methods to kill processes if they end up being bad so that it doesnt waste cpu.
  ListOfBadTargets = []
  for Target in ListOfTargets:
    # if they pass the initial tests, create their directories
    if not testTargetRegex(Target):
      ListOfBadTargets.append(Target)
  # now remove every bad target from our list
  for Target in ListOfBadTargets:
    ListOfTargets.remove(Target)
  ## Return the list of targets
  return ListOfTargets
  
### Function to make temp file and fill with basic cheader contents#
def makeTempFile(Target):
  subprocess.run(["touch", "/home/PingMaker/csv/"+Target+"/"+Target+".csv"])
  with open("/home/PingMaker/csv/"+Target+"/"+Target+".csv", "a") as TargetCSVFile:
    TargetCSVFile.write("timeofPing,packetLoss,responseTime,note")

### Function to create needed directories for code to work
def makeDirectories():
  subprocess.run(["mkdir", "/home/PingMaker/csv"])
  subprocess.run(["mkdir", "/home/PingMaker/errors"])
  subprocess.run(["mkdir", "/home/PingMaker/errors/Errors.txt"])

### Function to take a list of targets and set up their temp files
def targetFileSetup(ListOfTargets):
  # make directories if they are not already created, then add the file to those directories
  for Target in ListOfTargets:
    subprocess.run(["mkdir", "/home/PingMaker/csv/"+Target])
    makeTempFile(Target)

### Function to do a ping command, and return the output as an array of values. The array is: the time of ping, the packet loss, the response time, and any note outputted by the command#
def getPingArray(Target):
  # set up of variables and grabbing the result of the ping
  timeOfPing = time.strftime("%D:%H:%M:%S")
  packetLoss = "NA"
  responseTime = "NA"
  errorNote= "NA"
  output = getOutput("ping -c 1 " + Target)
  #parsing through results of ping to grab data. It will grab packet loss, response time, and any error it finds. It will then return the output
  for line in output:
    if "% packet loss" in line and "errors" not in line:
      packetLoss = line.split(', ')[2].split(" ")[0]
    elif "errors" in line:
      packetLoss = line.split(', ')[3].split(" ")[0]
    elif "Host Unreachable" in line or "Temporary failure" in line or "Name or service" in line or "Network is unreachable" in line:
      errorNote = line
    elif "bytes from" in line:
      responseTime = line[line.find("time=")+7:]
  return [timeOfPing,packetLoss,responseTime,errorNote]

### Function to rotate the log files so you dont have excessivly long logs, name the logs the timestamp they logged
def rotateLogs(tempFilePath, Target, timeSinceStart):
  # get the times turned to strings to add to the name of file
  timeNow = time.strftime("%D:%H:%M")
  timeNow = str(timeNow.replace("/","_").replace(":","-"))
  timeSinceStart = str(timeSinceStart.replace("/","_").replace(":","-"))
  newFilePath = "/home/PingMaker/csv/"+Target+"/"+timeSinceStart+"____"+timeNow+".csv"
  # rename the log file, then create a new temp file
  subprocess.run(["mv", tempFilePath, newFilePath])
  makeTempFile(Target)
  # if there are more than 6 logs (24 hours worth), remove the oldest (last modified) file
  fileCount = int(getOutput("ls /home/PingMaker/csv/"+Target+" | wc -l")[0])
  if count > 6:
    oldestFile = getOutput("ls -t /home/PingMaker/csv/"+Target+" | tail -1")[0]
    subprocess.run(["rm", "-f", "/home/PingMaker/csv/"+Target+"/"+oldestFile])

### Function to fix erred out targets
def fixInterrupted(tempFilePath, Target, timeSinceStart):
  timeNow = time.strftime("%D:%H:%M")
  timeNow = str(timeNow.replace("/","_").replace(":","-"))
  timeSinceStart = str(timeSinceStart.replace("/","_").replace(":","-"))
  newFilePath = "/home/PingMaker/csv/"+Target+"/"+timeSinceStart+"____"+timeNow+"_ERRORED.csv"
  subprocess.run(["mv", tempFilePath, newFilePath])

### Function to be threaded. This function handles the main process of pinging and storing file data
def PingMaker(Target):
  # make a boolean that will allow the program to run, if it errors too much and the boolean trips, end the process by breaking the loop
  lowErrors = True
  # grab the starting time of the function in seconds and the time in a diff format . This will be used to keep track of how long the function is running so we can do a time based log rotation
  referenceStart = time.time()
  timeSinceStart = time.strftime("%D:%H:%M")
  # we will set up a file name to be used by other code when appending to the file so I dont have to write the whole path over and over again#
  tempFilePath = "/home/PingMaker/csv/"+Target+"/"+Target+".csv"
  # Error Count, this is to count total errors, if total errors of a certain kind happen often, it will close the thread because it will nto ever succede
  errorCount = 0
  # Setting up the while statement to always run and continuously try pinging, otherwise if the event happens it will break the loop#
  while lowErrors:
    # Grab the info from a the ping output function
    pingArray = getPingArray(Target)
    # Write the data to the target file
    with open(tempFilePath, "a") as tempFile:
      tempFile.write("\n"+pingArray[0]+","+pingArray[1]+","+pingArray[2]+","+pingArray[3])
    # if there was an error note created, add to the count. 
    if "NA" not in pingArray[3]:
      errorCount += 1
      if errorCount >= 750:
        errWrite("Target thread closed due excessive errors for: " + Target)
        lowErrors = False
        #fix the name of the file so you know the timestamp
        fixInterrupted(tempFilePath, Target, timeSinceStart)
    #if no error created, tell the program to wait a second. this is because a succesfull ping will generally happen pretty quick, so this will limit the pings to about one every one or two seconds. 
    else:
      time.sleep(1)
      # now, check the time that the code has ran for, if its been about 4 hours rotate logs#
    if int((time.time()-referenceStart)/60/60) == 4:
      rotateLogs(tempFilePath, Target, timeSinceStart)
      timeOfStart = time.time()

########    ----   MAIN     ----    ####### MAYBE DO THE IF MAIN THING#
# sets up needed directories
makeDirectories()
# Get list of targets Make a directory and a csv file for every target in that list. then, add the header info to it
ListOfTargets = getTargets()
targetFileSetup(ListOfTargets)

# Start a thread per target. Each thread will ping the target and log to their own files.
for Target in ListOfTargets:
  PingThread = threading.Thread(target=PingMaker, args=(Target,))
  PingThread.start()


