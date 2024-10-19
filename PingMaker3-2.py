#### Setup ####
###Imports###
import time
import threading
import subprocess
import ipaddress
import re
import random

#### Function to turn cli output into an array, each line being an item in the array###
def getOutput(Command):
  temp = subprocess.Popen(Command, shell=True, stdout=subprocess.PIPE)
  output,error = temp.communicate()
  output = output.decode("utf-8")
  output = output.splitlines()
  return output

### Function to write errors to our error file ### LEAVE OUT THE BITS FOR RANDOM RETRYING FOR NOW AND WELL SEE HOW IT GOES
def errWrite(Message, Address):
  with open("/home/PingMaker/errors/Errors.txt", "a") as errfile:
    errfile.write("\n"+Message+Address)

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
      errWrite("Regex test failed for: ",Target)
      return False
      
###Function to create our temporary log file. It will start a subprocess and wait till the process is done
#def makeTempFile(Target):
#  proc = subprocess.run(["mkdir", "/home/PingMaker/csv/"+Target)
  
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
    if not testTargetRegex(target):
      ListOfBadTargets.append(Target)
  # now remove every bad target from our list
  for Target in ListOfBadTargets:
    ListOfTargets.remove(Target)
  ## Return the list of targets
  return ListOfTargets

### Function to take a list of targets and set up every file you would need for them
def targetFileSetup(ListOfTargets):
  # make directories if they are not already created
  subprocess.run(["mkdir", "/home/PingMaker/csv"])
  subprocess.run(["mkdir", "/home/PingMaker/errors"])
  for Target in ListOfTargets:
    subprocess.run(["mkdir", "/home/PingMaker/csv/"+Target])
    subprocess.run(["touch", "/home/PingMaker/csv/"+Target+"/"+Target+".csv"])
    with open("/home/PingMaker/csv/"+Target+"/"+Target+".csv", "a") as TargetCSVFile:
      TargetCSVFile.write("timeofPing,packetLoss,responseTime,note")

### Function to do a ping command, and return the output as an array of values. The array is: the time of ping, the packet loss, the response time, and any note outputted by the command#
def getPingArray(Target):
  # set up of variables and grabbing the result of the ping
  timeOfPing = time.strftime("%D:%H:%M:%S")
  packetLoss = "NA"
  responseTime = "NA"
  notes= "NA"
  output = getOutput("ping -c 1 " + Target)
  #parsing through results of ping to grab data
  for line in output:
    if "% packet loss" in line and "errors" not in line:
      packetLoss = line.split(', ')[2].split(" ")[0]
      if bytesFound == False:
        responseTime = "NA"
    elif "errors" in line:
      packetLoss = line.split(', ')[3].split(" ")[0]
      for line2 in output:
        if "Host Unreachable" in line:
          notes = "Destination Host Unreachable"     ###where im leaving off###
    elif "bytes from" in line:
      bytesFound = True
      responseTime = line[line.find("time")+6:]
### Function to be threaded. This function handles the main process of pinging and storing file data
def PingMaker(Target):
  # Get start an event. This event can be shared with functions, and if this event is tripped, this function will end to save resources. This will be used in the case of error handling, where it is clear pinging is a waste of reosurces.
  event = threading.Event()
  # grab the starting time of the function. This will be used to keep track of how long the function is running so we can do a time based log rotation
  timeOfStart = time.time()
  # we will set up a file name to be used by other code when appending to the file so I dont have to write the whole path over and over again#
  tempFileName = "/home/PingMaker/csv/"+Target+"/"+Target+".csv"
  # Setting up the while statement to always run and continuously try pinging, otherwise if the event happens it will break the loop#
  while True:
    # Grab the info from a the ping output function, and then check the time of how long the code has ran for
    
########    ----   MAIN     ----    ####### MAYBE DO THE IF MAIN THING

# Get list of targets Make a directory and a csv file for every target in that list. then, add the header info to it
ListOfTargets = getTargets()
targetFileSetup(ListOfTargets)

# Start a thread per target. Each thread will ping the target and log to their own files.
for Target in ListOfTargets:
  PingThread = threading.Thread(target=PingMaker, args=(Target,))
  PingThread.start()


