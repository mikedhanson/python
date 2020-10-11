import json
import socket
import requests
import time
from datetime import datetime
from influxdb import client as influxdb
from requests.auth import HTTPBasicAuth

interval = 6 # Sample period in seconds
influx_host = '192.168.1.x'
influx_port = '8086'
user = 'root'
password = 'password'
dbname = 'nextcloud'
log_measurement = 'nextcloud_stats'
username = "user"
passwd = "reallysuperlongpasswordthatissecure"
url = 'https://URL_hostname/ocs/v2.php/apps/serverinfo/api/v1/info?format=json'

client = influxdb.InfluxDBClient( influx_host, influx_port, user,password, dbname )

def getStats():
    count = 0
    while True:
        fields = dict()
        tags = dict()

        req = requests.get(url, auth=HTTPBasicAuth(username, passwd)).json()
        
        data = req['ocs']['data']
        nextcloud = req['ocs']['data']['nextcloud']
        
        #system info 
        fields['status'] = req['ocs']['meta']['status']
        fields['db_size'] = data['server']['database']['size']
        fields['apps_installed'] = nextcloud['system']['apps']['num_installed']
        fields['apps_updates_available'] = nextcloud['system']['apps']['num_updates_available']
        fields['mem_total'] = nextcloud['system']['mem_total']
        fields['version'] = nextcloud['system']['version']
        
        #user info
        fields['num_users'] = nextcloud['storage']['num_users']
        fields['active_users_5m'] = data['activeUsers']['last5minutes']
        fields['active_users_24h'] = data['activeUsers']['last24hours']

        fields.update(nextcloud['storage'])
        fields.update(nextcloud['shares'])

        tags['host'] = socket.gethostname()
        tags['webserver'] = data['server']['webserver']
        tags['php'] = data['server']['php']['version']
        #tags['name'] = name

        datapoints = [{
            "measurement": log_measurement,
            "tags": tags,
            "time": datetime.utcnow().isoformat(),
            "fields": fields
        }]

        #print('metrics: %s' % datapoints)
        try:
            client.write_points(datapoints, time_precision='m')
        except IOError:
            print("Oops!  Failed to post" % datapoints)
        count = count + 1
        print("Logs created this session: ", count )
        time.sleep(interval)

def main():
    print("Starting nextcloud scraper")
    print("Variables set: "+ 
    '\n interval (in seconds)        :: %s' % interval +
    '\n influx_host                  :: %s' % influx_host +
    '\n -e influx_port               :: %s' % influx_port +
    '\n -e user                      :: %s' % user +
    '\n -e dbname                    :: %s' % dbname +
    '\n -e log_measurement           :: %s' % log_measurement +
    '\n -e url                       :: %s' % url 
    )
    getStats()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        exit(0)
