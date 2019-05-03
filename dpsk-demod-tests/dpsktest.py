import matplotlib.pyplot as plt
f = open('12testdataunconnected.txt')


timestamps = []
values = []
for line in f:
    if line[0:2] == 'DS':
        pairs = line.split(';')
        del pairs[0]
        del pairs[1]
        for pair in pairs:
            try:
                timestamp, value = pair.split(',')
                timestamps.append(int(timestamp))
                values.append(int(value))
            except:
                continue

timestamps = list(map(lambda x: x-timestamps[0], timestamps))

def get_index_and_max(values):
    return max(range(len(values)), key=values.__getitem__) , max(values)

sampletimes = []
samplevalues = []
for n in range(0, 250000, 833):
    sliced = values[n:n+10]
    index, value = get_index_and_max(sliced)
    index += n
    sampletimes.append(timestamps[index])
    samplevalues.append(value)

def inPhaseHigh(basetime, timestamp, value):
    check  = (timestamp-basetime)%83
    if check > 60 or check < 20:
        return 0 #phase 0
    else:
        return 1 #phase 1

phases = []
basetime = sampletimes[0]
for n in range(0, len(samplevalues)):
    phases.append(inPhase(basetime, sampletimes[n], samplevalues[n]))

print(phases)


phasestring = ''
for n in phases:
    phasestring += str(n)
print(phasestring)

def phase_array_to_dpsk_string(phase_array):
    dpskstring = ''
    for i in range(0, len(phases)):
        if i< len(phases)-1:
            if (phases[i] != phases[i+1]):
                dpskstring += '1'
            else:
                dpskstring += '0'
    return dpskstring

dpskstring = phase_array_to_dpsk_string(phases)

print(dpskstring)

lastindex = 0
messagestarts = []
while(True):
    try:
        start = dpskstring.index('11111110', lastindex)
        print(start)
        messagestarts.append(start)
        lastindex = start+1
    except:
        break
print(messagestarts)

def retrieve_message(dpskstring, startindex):
    if len(dpskstring)-52 < startindex:
        return False
    bits = dpskstring[startindex:startindex+53]
    message = ''
    for i in range(0,13):
        byte = bits[(i*4):(i*4)+4]
        hexed = hex(int(byte,2))
        formatted = hexed[2]
        message += formatted
    #add the last bit
    message += hex(int(str(bits[52])+'000',2))[2]
    return bits, message

for n in messagestarts:
    print(retrieve_message(dpskstring, n))

#001110110100010101011101111011111000111101000111011011001000101001001010111101101100100101110110001100110100110000000010111110110101001001010001001110110111101010100000001001110001000111000110101100111101010001000110101100101001100001000100010011101111111001110100010011000010001011001110001011001100
# print(values[0])
# print(max(values))
# print(min(values))

# average = sum(values)/len(values)
# print(average)

# highlow = list(map(lambda x: (0,1)[x > average], values))

# #for 12.04Khz peak occurs every 83 microseconds
# def inPhase(timestamp, highlow):
#     if highlow == 1:
#         if timestamp%83 > 41.5:
#             return 0 #phase 0
#         else:
#             return 1
#     if highlow == 0:
#         if timestamp%83 < 41.5:
#             return 0 
#         else: 
#             return 1


# phases = []
# for i in range(0, len(values)):
#     phases.append(inPhase(timestamps[i], highlow[i]))

# temp = 0
# averagephases = []
# for i in range(400, len(phases)):
#     if i % 833 == 0:
#         averagephases.append(temp/i)
#     temp += phases[i]
#     i += 1



#plt.plot(list(range(0, len(phases))),phases)
#plt.show()
