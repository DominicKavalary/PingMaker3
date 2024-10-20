# Import the PingMaker script to get some of its functions
import PingMaker

# grab the time of interuption or service stopping
timeOfStop = time.time()

# grab the list of targets, then run though their directories and modify the name of any temp files to say INTERUPTED as to indicate the process was interupted
ListOfTargets = getTargets()
for Target in ListOfTargets:
  tempFilePath = "/home/PingMaker/csv/"+Target+"/"+Target+".csv"
  fixInterrupted(tempFilePath, Target, "INTERUPTED")

# log that events had stopped
errWrite("Service stopped or unexpectantly interupted, attempted to rename all temp files. Renamed csv directory to include time stopped.")

# rename the csv directory so that old target files dont get messed with
os.rename('/home/PingMaker/csv', '/home/PingMaker/csv_'+timeOfStop)
