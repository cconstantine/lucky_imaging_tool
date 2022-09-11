LIT Lucky Imaging Tool monitors your filepath as you image, it looks at the filename, which NINA can write the FWHM to. If the FWHM is above a certain threshold, then the file is removed. Along with that you have the ability to crop you can remove a percentage of the width and height, useful for maintaining low file size. 

To execute the raw python file follow the steps below: 

NOTE: Difference between MonitorNINA.py and LITforNINAusers.py -- MonitorNINA does not need NINA to be open and running to execute, LITforNINAusers needs NINA to execute and will stop running after NINA is closed. LIT Release 1 uses LITforNINA.py

In order to execute the script you must download Anaconda, found here: https://www.anaconda.com/ 

Once downloaded, please open cmd (windows) (command line) and type the following: 

``` sh
pip install -r requirements.txt
```

then: go to the directory the code is downloaded, in the cmd line type "cd path" ex: "cd H:\MyWorkPythonAll" 
then type, python3 monitorNINA.py and hit enter

possible errors: 

"Module not found (modulename)" 

to fix this just do pip install modulename
