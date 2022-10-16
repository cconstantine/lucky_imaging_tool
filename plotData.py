import pandas as pd
import matplotlib.pyplot as plt
import collections
df=pd.read_csv('catalog.csv')
Y=df['FWHMARCSEC']
X=[]
for i in range(len(Y)):
    X.append(i)
counter = collections.Counter(Y)
count=[counter[x] for x in sorted(counter.keys())]
Xax=counter.keys()
print(count)
plot1=plt.figure(1)
plt.xlabel("Image Index")
plt.ylabel("FWHM in Arcseconds")
plt.plot(X,Y)
plot2=plt.figure(2)
plt.xlabel('FWHM in Arcseconds')
plt.ylabel('Count')
plt.bar(Xax,count,align='center',width=0.1)
plt.show()
