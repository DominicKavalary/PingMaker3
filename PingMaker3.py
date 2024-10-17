#### Setup ####
###Imports###
import time
import threading
import subprocess
import ipaddress
import re

##Functions###
#subprocess outputgrab function#
def getOutput(Command):
  temp = subprocess.Popen(Command, shell=True, stdout=subprocess.PIPE)
  output,error = temp.communicate()
  output = output.decode("utf-8")
  output = output.splitlines()
  return output

# function to ping and return results to an array#
def getPingInfo(Address):
  timeOfPing = time.strftime("%D:%H:%M:%S")
  command = "ping -c 1 " + Address
  packetLoss = 0
  responseTime = ""
  output = getOutput(command)
  time.sleep(1)
  infoFound = False
  for line in output:
    if "% packet loss" in line:
      infoFound = True
      packetLoss = line.split(', ')[2].split(" ")[0]
    elif "bytes from" in line:
      infoFound = True
      responseTime = line[line.find("time"):]
  if infoFound == True:
    return [timeOfPing,packetLoss,responseTime]
  elif testTargetDeep(Address) == False:
# if the input isnt found, add the address to the error file. Try and find a way of killing the processes instead. such as, when you first make the process can you create a processname, then search for that process name and kill it
    with open("/home/PingMaker/errors/errlist.txt", "a") as errfile:
      errfile.write("\nDeep ping test failed for: "+Address+" at "+timeOfPing+", check format of address")
      time.sleep(60)
  else:
    with open("/home/PingMaker/errors/errlist.txt", "a") as errfile:
      errfile.write("\nUnknown error for: "+Address+" at "+timeOfPing)
      time.sleep(60)
  
# write a function where ti testrs if its an error or not then if it is do add it if it isnt dont add it to targets#
def testTargetDeep(Address):
#look for info in the output
  command = "ping -c 1 " + Address
  output = getOutput(command)
  infoFound = False
  for line in output:
      if "% packet loss" in line:
        infoFound = True
      elif "bytes from" in line:
        infoFound = True
  # regardless, return the value of infoFound so the code knows what to do
  return infoFound

def testTargetRegex(Address):
  regex = "^((25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])\.){3}(25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])$"
  if re.search(regex, Address):
    return True
  else:
    regex = "[a-zA-Z0-9@:%._\\+~#?&//=]{2,256}\\.[a-z]" + "{2,6}\\b([-a-zA-Z0-9@:%._\\+~#?&//=]*)"
    if re.search(regex,Address):
      return True
    else:
      with open("/home/PingMaker/errors/errlist.txt", "a") as errfile:
        errfile.write("\nRegex test failed for: "+Address+", check format of address")
      False
  
#Ping and write thread function#
def PingandWrite(Address):
  timeOfStart = time.time()
  while 1 == 1:
# get ping response and store in array
    pingArray = getPingInfo(Address)
    tempFileName = "/home/PingMaker/csv/"+Address+"/"+Address+".csv"
# open the target's directory and append to its data file
    with open(tempFileName, "a") as tmp:
      tmp.write("\n"+pingArray[0]+","+pingArray[1]+","+pingArray[2])
# if it has been 6 hours since the file has been rotated, take the current temp file and change its name so you can start making a new temp file
      if int((time.time()-timeOfStart)/60/60) == 6:
        newFileileName = Address+"_"+str(timeOfPing).replace("/","_").replace(":","-")+".csv"
        subprocess.Popen("mv "+tempFileName+" /home/PingMaker/csv/"+Address+"/"+newFileName), shell=True, stdout=subprocess.PIPE)
        timeOfStart = time.time()
# now make a new temp file
        with open(tempFileName, "a+") as tmpNew:
          tmpNew.write("timeofPing,packetLoss,responseTime")
# if no info was found, create an error file. then mark the errorFileNotCreated to False so that it doesnt keep writing to the file every time. Once again, make a function to test all addresses beforehand, and for the ones that fail add their addresses to a single text file with the name including the timestamp of when the error checking happened


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
for target in ListofTargets:
  if testTargetRegex(target):
    subprocess.Popen("mkdir /home/PingMaker/csv/"+target, shell=True, stdout=subprocess.PIPE)
  else:
    ListofTargets.remove(target)
time.sleep(2)
# now for every target in your list, append the csv header info to the file
for target in ListofTargets:
  with open("/home/PingMaker/csv/"+target+"/"+target+".csv", "a+") as statfilecsv:
    statfilecsv.write("timeofPing,packetLoss,responseTime")
    
####multithres ping targets and wirte to file###
# for every address in your list of targets, start their own ping and write subprocess for them to run
for Address in ListofTargets:
  PingThread = threading.Thread(target=PingandWrite, args=(Address,))
  PingThread.start()


#####look into interupted code, maybe add an exit thing that will look in all target directories, then rename the temp file to tempfile_interupted or something similar.
