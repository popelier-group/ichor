import os
import shutil

XYZDir  = "XYZs"
origDir =  "orig"
files = list()
origFiles = list()
for file in os.listdir(XYZDir):
    if file.endswith(".xyz"):
        files.append(os.path.join(XYZDir,file))

for file in os.listdir(origDir):
    origFiles.append(os.path.join(origDir,file))

list_file = open("list.txt","w")
countDir = 0
for file in files:
    countDir+=1
    geomID=os.path.split(file)[1].split("GEOM")[1].split(".xyz")[0]
    newDir = os.path.join(os.getcwd(),"RUN"+geomID)
    if os.path.isdir(newDir):
        shutil.rmtree(newDir)
    os.mkdir(newDir)
    shutil.copy(file,os.path.join(newDir,"GLUTATHIONE.xyz"))
    for file in origFiles:
        if not os.path.isdir(file):
            shutil.copy(file,newDir)
        else:
            shutil.copytree(file,os.path.join(newDir,os.path.split(file)[1]))
    list_file.write("RUN"+str(countDir-1)+"/\n")
list_file.close()

