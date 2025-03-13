from common.serialProcess import SerialProcess

sp = SerialProcess()
sp.open_port("COM10", 115200)

while True:
    reading = sp.read()
    print(reading)
