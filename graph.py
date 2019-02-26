import matplotlib.pyplot as plt

x = []
y = []

n = 1
with open('sample.txt','r') as file:
    for row in file:
        x.append(n)
        v = row.replace('\n','')
        y.append(float(v))
        n += 1
        if(n > 100):
            break


plt.plot(x,y)
plt.xlabel('x')
plt.ylabel('value')
plt.title('ADC Voltage Readings')
plt.show()
