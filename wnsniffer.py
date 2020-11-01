# -----------------------------------------------------------
# aquire serial data from tty and writes the data to influx
#
# (C) 2020 Steven Hansen, Stuttgart, Germany
# Released under GNU Public License (GPL)
# email: mail@shansen-online.de
# -----------------------------------------------------------

# -*- coding: utf-8 -*-


# -----------------------------------------------------------
# import libraries
# -----------------------------------------------------------

import argparse
import copy
import serial
import time
import re
import threading
import json

from influxdb import InfluxDBClient
from influxdb import SeriesHelper

# -----------------------------------------------------------
# global variables
# -----------------------------------------------------------

channel = 1
stick_port = '/dev/ttyACM0' # wavenet stick tty port

db_host='10.0.0.4' # database connection is in the local network, assumes vpn connection
db_port=8086

dbname = 'wavenet_stick'

# -----------------------------------------------------------
# Instantiate a connection to the InfluxDB
# Instantiate a connection to the tty
# -----------------------------------------------------------

ser = serial.Serial(stick_port, baudrate = 9600, dsrdtr=False)
ser.timeout=0.01

client = InfluxDBClient(db_host, db_port, dbname)

# -----------------------------------------------------------
# flush array of dictionaries to influx, this is done in
# a seperate thread to avoid data losses due to buffer limits
# -----------------------------------------------------------
def writeToDatabase(dict_list):

		time.sleep(1)

                while True:

                        try:
				time.sleep(0.05)
                                #print("count:", len(dict_list))
                                try:
                                        if len(dict_list) >= 200:			# wait for at least 100 telegrams before writing
						buffer = copy.deepcopy(dict_list)	# clear dict_list before writing to db because writing 
											# datapoints might take longer than serial can buffer data 
						del dict_list[:]
						# print("write to db:", buffer[0]['fields'])
                                                client.write_points(buffer, database=dbname, batch_size=200, time_precision='ms')
					else:
						continue
                                except:
                                        pass
                                        # raise

                        except:
                                pass
				# raise

# -----------------------------------------------------------
# get byte by byte from serial and dump it
# -----------------------------------------------------------
def readData(stick_port):
        buffer = ""
        while True:
		time.sleep(0.0001) 	# give the cpu some time to do other things
					# on pi v1 this will be 0.118 MIPS 
                oneByte = stick_port.read(1)
                if oneByte == b"\n" :    # method should returns bytes
                        return buffer
                else:
                        try:
                                buffer += oneByte.decode("ascii")
                        except:
                                pass

# -----------------------------------------------------------
# main()
# -----------------------------------------------------------
def main():

        #client.create_database(dbname) # uncomment to create a new db, i created it with web ui "chronograph"

	# sending "!fc{channel}ra1" 
        time.sleep(1)
        ser.write("!f"+b"\n")
        readData(ser)
        # print("rec:", readData(ser))
        ser.write("c1"+b"\n")
        readData(ser)
        # print("rec:", readData(ser))
        ser.write("ra1"+b"\n")
        readData(ser) #
        # print("rec:", readData(ser))

        time.sleep(1)

        dict_body = { "measurement": "wavenet_rssi_values", "tags": { "host": "server01" }, "fields": { "noise": 0, "signal": 0, "content": "" }, "time": int(time.time() * 1000)  }

        dict_list = []

        t = threading.Thread(target=writeToDatabase, args=(dict_list, ))
        t.daemon = True
        t.start()

        print("db thread started")	# some sign of life

        while True:

                str1 = readData(ser).encode('ascii', 'ignore')

                try:
                        str2 = re.findall(r'[0-9]+', re.findall(r'^\[S\] -[0-9]+', str1)[0])[0]
                        int2 = int(filter(str.isdigit, (str2.encode('ascii', 'ignore'))))*-1

                except:
                        int2 = 0
                        # print("no int2")
                        pass

                try:
                        str3 = re.findall(r'[0-9]+', re.findall(r'^RSSI:-[0-9]+', str1)[0])[0]
                        int3 = int(filter(str.isdigit, (str3.encode('ascii', 'ignore'))))*-1

                except:
                        int3 = 0
                        # print("no int3")
                        pass

                try:
                        data = re.findall(r'^RSSI:.*', str1)[0]

                except:
                        data = ""
                        # print("no data")
                        pass

                try:

                        dict_body = { "measurement": "wavenet_rssi_values", "tags": { "host": "server01" }, "fields": { "noise": int2 , "signal": int3, "content": data }, "time": int(time.time() * 1000)  }
                        # print("dict print:", dict_body['fields'])
                        dict_list.append(dict_body)

                except:
                        pass

                #print("Drop database: " + dbname)
                #client.drop_database(dbname)


if __name__ == '__main__':
        #args = parse_args()
        main() #host=args.host, port=args.port)

# -----------------------------------------------------------
#
# -----------------------------------------------------------

