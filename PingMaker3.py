#### Setup ####
###Imports###
import time
import threading
import subprocess
import ipaddress
import re
import random

##Functions###
#Write to error file#
#########################THIS MIGHT BE ALMOST COMPLETELY UNNECESARY#############
def errWrite(Address, Message):
  errorWrote = False
  for i in range(10):
    if errorWrote == False:
      try:
        with open("/home/PingMaker/errors/errlist.txt", "a") as errfile:
          errfile.write("\n"+Message+Address)
          errorWrote = True
      except:
          time.sleep(random.randint(1, 15))
    else:
      break
  if errorWrote == False:
    with open("/home/PingMaker/errors/Unknown.txt", "a") as errfile:
      errfile.write("\n"+"Failure to write error for: "+Address)

#subprocess outputgrab function#
def getOutput(Command):
  temp = subprocess.Popen(Command, shell=True, stdout=subprocess.PIPE)
  output,error = temp.communicate()
  output = output.decode("utf-8")
  output = output.splitlines()
  return output

# write a function where ti testrs if its an error or not then if it is do add it if it isnt dont add it to targets#
def testTargetDeep(Address,timeOfPing,output):
#look for info in the output
  lossFound = False
  bytesFound = False
  errMessageFound = False
  message=""
  for line in output:
      if "% packet loss" in line:
        lossFound = True
      elif "bytes from" in line:
        bytesFound = True
      elif "" in line:
        errMessageFound = True
        message = line.replace("\n","")
  if not lossFound or not bytesFound:
    errWrite(Address,"Deep Ping test failed at"+timeOfPing+", no Packet Loss found or no Bytes returned: ")
    if errMessageFound:
      errWrite(Address,"Deep Ping test failed at"+timeOfPing+", error message given: "+message+"")
  else:
    errWrite(Address, "Unknown fail at"+timeOfPing+",: ")

# function to ping and return results to an array#
def getPingInfo(Address):
  timeOfPing = time.strftime("%D:%H:%M:%S")
  command = "ping -c 1 " + Address
  packetLoss = ""
  responseTime = ""
  output = getOutput(command)
  lossFound = False
  bytesFound = False
  for line in output:
    if "% packet loss" in line:
      lossFound = True
      packetLoss = line.split(', ')[2].split(" ")[0]
      if bytesFound == False:
        responseTime = "NA"
    elif "bytes from" in line:
      bytesFound = True
      responseTime = line[line.find("time"):]
  if lossFound:
    return [timeOfPing,packetLoss,responseTime]
  else:
    testTargetDeep(Address,timeOfPing,output)
    return ["na","na","na"]
    
##Fast regex test for address validation###
def testTargetRegex(Address):
  regex = r"^((25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])\.){3}(25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])$"
  if re.search(regex, Address):
    return True
  else:
    regex = "[a-zA-Z0-9@:%._\\+~#?&//=]{2,256}\\.[a-z]" + "{2,6}\\b([-a-zA-Z0-9@:%._\\+~#?&//=]*)"
    if re.search(regex,Address):
      return True
    else:
      errWrite(Address,"Regex test failed for: ")
      return False
#Ping and write sub thread for rapid pings even on failures#
def SubPingandWrite(Address,TmpName):
  pingArray = getPingInfo(Address)
# open the target's directory and append to its data file
  with open(TmpName, "a") as tmp:
    tmp.write("\n"+pingArray[0]+","+pingArray[1]+","+pingArray[2])

#Ping and write thread function#
def MainPingandWrite(Address):
  print("thread for "+Address+" Started")    
  timeOfStart = time.time()
  tempFileName = "/home/PingMaker/csv/"+Address+"/"+Address+".csv"
  while 1 == 1:
# get ping response and store in array
    SubPingThread = threading.Thread(target=SubPingandWrite, args=(Address,tempFileName,))
    SubPingThread.start()
    time.sleep(1)
# if it has been 6 hours since the file has been rotated, take the current temp file and change its name so you can start making a new temp file
    if int((time.time()-timeOfStart)/60/60) == 6:
      newFileName = Address+"_"+str(time.strftime("%D:%H:%M:%S")).replace("/","_").replace(":","-")+".csv"
      subprocess.Popen("mv "+tempFileName+" /home/PingMaker/csv/"+Address+"/"+newFileName, shell=True, stdout=subprocess.PIPE)
      timeOfStart = time.time()
# now make a new temp file
      with open(tempFileName, "a+") as tmpNew:
        tmpNew.write("timeofPing,packetLoss,responseTime")
      count = int(getOutput("ls /home/PingMaker/csv/"+Address+" | wc -l")[0])
      if count > 6:
        oldestFile = getOutput("ls -t /home/PingMaker/csv/"+Address+" | tail -1")[0]
        subprocess.Popen("rm -f /home/PingMaker/csv/"+Address+"/"+oldestFile, shell=True, stdout=subprocess.PIPE)
        with open("/home/PingMaker/csv/"+Address+"/"+"rotatedlogs.txt", "a+") as logfile:
          logfile.write("\n"+oldestFile)
          
####MAIN####
####Create Directorys#####
subprocess.Popen("mkdir /home/PingMaker/csv", shell=True, stdout=subprocess.PIPE)
subprocess.Popen("mkdir /home/PingMaker/errors", shell=True, stdout=subprocess.PIPE)
time.sleep(1)

# grab a list of targets from the target file
ListofTargets = []
with open("/home/PingMaker/PingTargets.txt", "r") as targetFile:
  for line in targetFile:
# check if there is an address range deliniated by cidr notation, if so, then get all available addresses and add them individually to list of targets
    if "/" in line:
      usableSubnet = [str(ip) for ip in ipaddress.IPv4Network(line.replace("\n",""))]
      for ip in usableSubnet[1:-1]:
        ListofTargets.append(str(ip))
    else:
# if there is no address range, add it as a singular host
      ListofTargets.append(line.replace("\n",""))
# for every target in the list you just made, test them to see if they are valid targets, if so make their target directories. this is where their csv files will be stored.
listofBAD = []
for target in ListofTargets:
  if testTargetRegex(target):
    proc = subprocess.Popen("mkdir /home/PingMaker/csv/"+target, shell=True, stdout=subprocess.PIPE)
    proc.wait()
  else:
    listofBAD.append(target)
  time.sleep(1)
for target in listofBAD:
  ListofTargets.remove(target)
# now for every target in your list, append the csv header info to the file
for target in ListofTargets:
  with open("/home/PingMaker/csv/"+target+"/"+target+".csv", "w+") as statfilecsv:
    statfilecsv.write("timeofPing,packetLoss,responseTime")
print("All files created")    
####multithres ping targets and wirte to file###
# for every address in your list of targets, start their own ping and write subprocess for them to run
for Address in ListofTargets:
  PingThread = threading.Thread(target=MainPingandWrite, args=(Address,))
  PingThread.start()
print("All main processes created")  

#####look into interupted code, maybe add an exit thing that will look in all target directories, then rename the temp file to tempfile_interupted or something similar.
###find out why message errors arent populatinmg the errfile
dont do the wait after making directories, do a sleep for 2 seconds after the last call
