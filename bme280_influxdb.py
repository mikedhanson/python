
import bme280
import smbus2
import time
from influxdb import client as influxdb

sensor_location = 'bedroom'
interval = 60 # Sample period in seconds
influx_host = '192.168.1.13'
influx_port = '8086'
user = 'root'
password = 'root'
dbname = 'bme280'
log_measurement = 'bme_stats'

client = influxdb.InfluxDBClient(influx_host, influx_port, user, password, dbname)

port = 1
address = 0x77
bus = smbus2.SMBus(port)
bme280.load_calibration_params(bus, address)

def getStats():
    count = 0
    while True:
        bme280_data = bme280.sample(bus,address)
        humidity = bme280_data.humidity
        pressure = bme280_data.pressure
        ambient_temp = bme280_data.temperature
        data = [
            {
            "measurement": log_measurement,
                "tags": {
                    "location": sensor_location,
                },
                "fields": {
                    "temperature" : ambient_temp,
                    "humidity" : humidity,
                    "pressure" : pressure
                }
            }
        ]
        #print('bme280 log metrics: %s' % data)
        client.write_points(data)
        count = count + 1
        print("Logs created this session: ", count )
        time.sleep(interval)


def main():
    print("Starting bme2influx...")
    print("Variables set: "+ 
    '\n interval (in seconds)        :: %s' % interval +
    '\n influx_host                  :: %s' % influx_host +
    '\n -e influx_port               :: %s' % influx_port +
    '\n -e user                      :: %s' % user +
    '\n -e dbname                    :: %s' % dbname +
    '\n -e log_measurement           :: %s' % log_measurement +
    '\n -e sensor_location           :: %s' % sensor_location +
    '\n -e address                   :: %s' % address 
    )
    getStats()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        exit(0)
