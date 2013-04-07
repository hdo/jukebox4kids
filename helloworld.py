import serial
ser = serial.Serial('/dev/pts/0', 115200)
ser.write("hello world")
ser.close()
