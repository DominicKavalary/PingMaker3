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
def testTargetDeep(Address):
#look for info in the output
  command = "ping -c 1 " + Address
  output = getOutput(command)
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
    errWrite(Address,"Deep Ping test failed, no Packet Loss found or no Bytes returned: ")
    return False
  elif errMessageFound:
    errWrite(Address,"Deep Ping test failed, error message given: "+message+"")
    return False
  elif lossFound and bytesFound:
    return True
  else:
    errWrite(Address, "Unknown for: ")
  print("the fuck "+Address)
  return False

# function to ping and return results to an array#
def getPingInfo(Address):
  print("getting ping for "+Address)    
  timeOfPing = time.strftime("%D:%H:%M:%S")
  command = "ping -c 1 " + Address
  packetLoss = ""
  responseTime = ""
  output = getOutput(command)
  time.sleep(1)
  lossFound = False
  bytesFound = False
  for line in output:
    print(line)
    if "% packet loss" in line:
      lossFound = True
      packetLoss = line.split(', ')[2].split(" ")[0]
      if bytesFound == False:
        responseTime = line.split(', ')[3].split(" ")[1]
    elif "bytes from" in line:
      bytesFound = True
      responseTime = line[line.find("time"):]
  if lossFound:
    return [timeOfPing,packetLoss,responseTime]
  elif testTargetDeep(Address) == False:
# if the input isnt found, add the address to the error file. Try and find a way of killing the processes instead. such as, when you first make the process can you create a processname, then search for that process name and kill it
    time.sleep(60)
    return ["na","na","na"]
  else:
    errWrite(Address,"Unknown error for: "+Address+" at "+timeOfPing)
    time.sleep(60)
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
  
#Ping and write thread function#
def PingandWrite(Address):
  print("thread for "+Address+" Started")    
  timeOfStart = time.time()
  tempFileName = "/home/PingMaker/csv/"+Address+"/"+Address+".csv"
  while 1 == 1:
# get ping response and store in array
    pingArray = getPingInfo(Address)
# open the target's directory and append to its data file
    with open(tempFileName, "a") as tmp:
      tmp.write("\n"+pingArray[0]+","+pingArray[1]+","+pingArray[2])
# if it has been 6 hours since the file has been rotated, take the current temp file and change its name so you can start making a new temp file
      if int((time.time()-timeOfStart)/60/60) == 6:
        newFileileName = Address+"_"+str(timeOfPing).replace("/","_").replace(":","-")+".csv"
        subprocess.Popen("mv "+tempFileName+" /home/PingMaker/csv/"+Address+"/"+newFileName, shell=True, stdout=subprocess.PIPE)
        timeOfStart = time.time()
# now make a new temp file
        with open(tempFileName, "a+") as tmpNew:
          tmpNew.write("timeofPing,packetLoss,responseTime")

####MAIN####
####Create Directorys#####
subprocess.Popen("mkdir /home/PingMaker/csv", shell=True, stdout=subprocess.PIPE)
subprocess.Popen("mkdir /home/PingMaker/errors", shell=True, stdout=subprocess.PIPE)
time.sleep(1)

# grab a list of targets from the target file
ListofTargets = []
with open("/home/PingMaker/PingMakerTargets.txt", "r") as targetFile:
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
  PingThread = threading.Thread(target=PingandWrite, args=(Address,))
  PingThread.start()
print("All processes created")  

#####look into interupted code, maybe add an exit thing that will look in all target directories, then rename the temp file to tempfile_interupted or something similar.
