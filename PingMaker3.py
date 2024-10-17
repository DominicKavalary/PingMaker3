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

#Ping and write thread function#
def PingandWrite(Address):
  errorFileNotCreated = True
  while 1 == 1:
    timeOfPing = time.strftime("%D:%H:%M:%S")
    command = "ping -c 1 " + Address
    output = getOutput(command)
    infoFound = False
    packetLoss = 0
    responseTime = ""
    for line in output:
      if "% packet loss" in line:
        packetLoss = line.split(', ')[2].split(" ")[0])
      elif "bytes from" in line:
        infoFound = True
        responseTime = line[line.find("time"):]
    if infoFound:
      time.sleep(1)
      with open("/home/PingMaker/csv/"+Address+".csv", "a") as statfilecsv:
        statfilecsv.write("\n"+timeofPing+","+packetLoss+","+responseTime)
    else:
      if errorFileNotCreated:
        with open("/home/PingMaker/errors/"+Address, "a") as errfile:
          errfile.write("\nNo info found for: "+Address+", check format of address")
        errorFileNotCreated = False


####Create Directorys#####
subprocess.Popen("mkdir /home/PingMaker/csv", shell=True, stdout=subprocess.PIPE)
subprocess.Popen("mkdir /home/PingMaker/errors", shell=True, stdout=subprocess.PIPE)
time.sleep(1)
####MAIN####
ListofTargets = []
with open("/home/PingMaker/PingMakerTargets.txt", "r") as targetFile:
  for line in targetFile:
    if "/" in line:
      usableSubnet = [str(ip) for ip in ipaddress.IPv4Network(line.replace("\n",""))]
      for ip in usableSubnet[1:-1]:
        ListofTargets.append(str(ip))
    else:
      ListofTargets.append(line.replace("\n",""))

for target in ListofTargets:
  with open("/home/PingMaker/csv/"+target+".csv", "a+") as statfilecsv:
    statfilecsv.write("timeofPing,packetLoss,responseTime")
####multithres ping targets and wirte to file###
# never stop until script is canceled
for Address in ListofTargets:
  PingThread = threading.Thread(target=PingandWrite, args=(Address,))
  PingThread.start()
