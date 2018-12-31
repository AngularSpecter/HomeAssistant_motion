#!/usr/bin/python

import sys
import json
import pycurl
import getopt

API_PASSWORD = " "

base_url =  'http://192.168.1.3:8123/api/services/mqtt/publish?api_password={}'.format( API_PASSWORD )

opts, args = getopt.getopt( sys.argv[1:], 'e:c:w:h:x:y:e:p:n:', ['status=', 'cam_id=', 'width=', 'height=', 'x=', 'y=', 'event_id=', 'pixels=', 'noise='  ])

payload = {}
payload[ 'topic' ] =  "home/downstairs/playroom/sensor/motion"
payload[ 'retain'] =  "True"

data_payload = {}
data_payload[ 'status']    =  "MOTION"
data_payload[ 'cam_id' ]   = ''
data_payload[ 'width' ]    = ''
data_payload[ 'height' ]   = ''
data_payload[ 'x' ]        = ''
data_payload[ 'y' ]        = ''
data_payload[ 'event_id' ] = ''
data_payload[ 'pixels' ]   = ''
data_payload[ 'noise' ]    = ''

for opt, arg in opts:
  opt = opt.replace("-","")
  data_payload[ opt ] = arg

payload['payload'] = json.dumps( data_payload )

json_string = json.dumps( payload )

request = pycurl.Curl()
request.setopt( pycurl.WRITEFUNCTION, lambda x: None )
request.setopt( request.URL, base_url )
request.setopt( request.HTTPHEADER, ["Content-Type: application/json"] )
request.setopt( request.POSTFIELDS, json_string )

request.perform()
request.close()
