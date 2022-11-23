
LIT Lucky Imaging Tool monitors your filepath as you image, it looks at each image and if the FWHM is too high, will delete it. 

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
