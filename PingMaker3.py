#### Setup ####
###Imports###
import time
import threading
import subprocess
import ipaddress

##Functions###
#subprocess outputgrab function#
def getOutput(Command):
  temp = subprocess.Popen(Command, shell=True, stdout=subprocess.PIPE)
  output,error = temp.communicate()
  output = output.decode("utf-8")
  output = output.splitlines()
  return output

# write a function where ti testrs if its an error or not then if it is do add it if it isnt dont add it to targets

#Ping and write thread function#
def PingandWrite(Address):
  timeOfStart = time.time()
  errorFileNotCreated = True
  while 1 == 1:
# Set up variables, get ping response
    timeOfPing = time.strftime("%D:%H:%M:%S")
    command = "ping -c 1 " + Address
    output = getOutput(command)
    infoFound = False
    packetLoss = 0
    responseTime = ""
    tempFileName = "/home/PingMaker/csv/"+Address+"/"+Address+".csv"
# Find info from ping output
    for line in output:
      if "% packet loss" in line:
        packetLoss = line.split(', ')[2].split(" ")[0]
      elif "bytes from" in line:
        infoFound = True
        responseTime = line[line.find("time"):]
# if info is found, wait a sec before doing another ping, then, open the target's directory and append to its data file
    if infoFound:
      time.sleep(1)
      with open(tempFileName, "a") as tmp:
        tmp.write("\n"+timeOfPing+","+packetLoss+","+responseTime)
# if it has been 6 hours since the file has been rotated, take the current temp file and change its name so you can start making a new temp file
      if int((time.time()-timeOfStart)/60/60) == 6:
        newFileileName = Address+"_"+str(timeOfPing).replace("/","_").replace(":","-")+".csv"
        subprocess.Popen("mv "+tempFileName+" /home/PingMaker/csv/"+Address+"/"+newFileName), shell=True, stdout=subprocess.PIPE)
        timeOfStart = time.time()
# now make a new temp file
        with open(tempFileName, "a+") as tmpNew:
          tmpNew.write("timeofPing,packetLoss,responseTime")
# if no info was found, create an error file. then mark the errorFileNotCreated to False so that it doesnt keep writing to the file every time. Once again, make a function to test all addresses beforehand, and for the ones that fail add their addresses to a single text file with the name including the timestamp of when the error checking happened
    else:
      if errorFileNotCreated:
        with open("/home/PingMaker/errors/"+Address, "a") as errfile:
          errfile.write("\nNo info found for: "+Address+", check format of address")
        errorFileNotCreated = False
      time.sleep(60) # for now do a wait of 60 seconds before it tries again, in the future make the process temrinate itself, OR make the functon to test all pings beforehand to validate targets, and remove invalid from the list of targets so you dont even have to do this here.


####Create Directorys#####
subprocess.Popen("mkdir /home/PingMaker/csv", shell=True, stdout=subprocess.PIPE)
subprocess.Popen("mkdir /home/PingMaker/errors", shell=True, stdout=subprocess.PIPE)
time.sleep(1)
####MAIN####
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
# for every target in the list you just made, make their target directories. this is where their csv files will be stored. Maybe add a check before this to see if every target is valid.
for target in ListofTargets:
  subprocess.Popen("mkdir /home/PingMaker/csv/"+target, shell=True, stdout=subprocess.PIPE)
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
