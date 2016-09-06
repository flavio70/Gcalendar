#!/usr/bin/python
#
# Copyright 2012 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import RPi.GPIO as GPIO
import httplib2
import socks
import sys,os
import time
from datetime import datetime
import re

from apiclient.discovery import build
from oauth2client import tools, client, file
from oauth2client.file import Storage
from oauth2client.client import AccessTokenRefreshError
from oauth2client.client import OAuth2WebServerFlow

from apscheduler.schedulers.background import BackgroundScheduler #this will let us check the calender on a regular interval



# argparse module needed for flag settings used in oaut2 autetication process
# by tools.run_flow procedure
try:
  import argparse
  flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
  flags = None


currPath = os.path.dirname(os.path.realpath(__file__)) + '/'


#LOG ON LOGFILE status
def logStatus(text):
	with open("/var/log/gcalendar/status.log","a+") as f: 
		f.write(str(datetime.now())+" "+text+"\n")

#LOG ON LOGFILE error
def logError():
	exc_type, exc_obj, tb = sys.exc_info()
	f = tb.tb_frame
	lineno = tb.tb_lineno
	filename = f.f_code.co_filename
	linecache.checkcache(filename)
	line = linecache.getline(filename, lineno, f.f_globals)

	text = "EXCEPTION IN (" + str(filename) + ", LINE " + str(lineno) + " '" + str(line.strip()) + "'):" + str(exc_obj);
	with open("/var/log/gcalendar/error.log","a+") as f: 
		f.write(str(datetime.now())+" "+text+"\n")

# The scope URL for read/write access to a user's calendar data
SCOPES = 'https://www.googleapis.com/auth/calendar'
CAL_ID = 'xxxxxxxxxxxxxxxxxxxxxxx@group.calendar.google.com'


# proxy settings to be used in case we are under firewall
# httpclient must be also used when calling tools.run_flow
#
# Uncomment the following 4 lines and fill the PROXY_IP & PROXY_PORT vars
# in case you are using a proxy
PROXY_IP='xxx.xxx.xxx.xxx'
PROXY_PORT=xxxx
socks.setdefaultproxy(socks.PROXY_TYPE_HTTP, PROXY_IP, PROXY_PORT)
socks.wrapmodule(httplib2)

# Create an httplib2.Http object to handle our HTTP requests
# httpclient must be also used when calling tools.run_flow in case of proxy usage
httpclient = httplib2.Http()

# Create a Storage object. This object holds the credentials that your
# application needs to authorize access to the user's data. The name of the
# credentials file is provided. If the file does not exist, it is
# created. This object can only hold credentials for a single user, so
# as-written, this script can only handle a single user.
store = file.Storage(currPath + 'storage.json')
print('\nGetting calendar credentials (Oauth2 authorization process)')
logStatus('\nGetting calendar credentials (Oauth2 authorization process)')

# The get() function returns the credentials for the Storage object. If no
# credentials were found, None is returned.
creds = store.get()

if not creds or creds.invalid:
  # Create a flow object. This object holds the client_id, client_secret, and
  # scope. It assists with OAuth 2.0 steps to get user authorization and
  # credentials.
  print('No Credentials were found\n Starting OAuth Process to get them ...')
  logStatus('No Credentials were found\n Starting OAuth Process to get them ...')
  flow = client.flow_from_clientsecrets(currPath + 'client_secret.json',SCOPES)

  # If no credentials are found or the credentials are invalid due to
  # expiration, new credentials need to be obtained from the authorization
  # server. The oauth2client.tools.run_flow() function attempts to open an
  # authorization server page in your default web browser. The server
  # asks the user to grant your application access to the user's data.
  # If the user grants access, the run_flow() function returns new credentials.
  # The new credentials are also stored in the supplied Storage object,
  # which updates the credentials.dat file.

  creds = tools.run_flow(flow,store,flags,httpclient) \
          if flags else tools.run(flow,store,httpclient)

else:
  print('Valid Credentials were found...')
  logStatus('Valid Credentials were found...')
  
# authorize http object
# using the credentials.authorize() function.

print('Authorizing...')
logStatus('Authorizing...')
httpclient = creds.authorize(httpclient)
print('...Done\n')
logStatus('...Done\n')

# The apiclient.discovery.build() function returns an instance of an API service
# object can be used to make API calls. The object is constructed with
# methods specific to the calendar API. The arguments provided are:
#   name of the API ('calendar')
#   version of the API you are using ('v3')
#   authorized httplib2.Http() object that can be used for API calls
service = build('calendar', 'v3', http=httpclient)


# settings for GPIOs
GPIO.setmode(GPIO.BCM)

# init list with pin numbers

pinList = [2, 3, 4, 5, 6, 7, 8, 9]

# loop through pins and set mode and state to 'low'

for i in pinList: 
    GPIO.setup(i, GPIO.OUT) 
    GPIO.output(i, GPIO.HIGH)





def runEvent(event,duration):

  print('Event: %s scheduled to run at this time'%event.get('summary','No Summary'))
  #logStatus('Event: %s scheduled to run at this time'%event.get('summary','No Summary'))
  #managing Google calendar event
  curr_event_descr = event.get('description','NO DESCRIPTION')
  if re.search('.*--DONE--.*',curr_event_descr):
    print('\tevent already  managed')
    logStatus('\tevent already  managed')
  else:
    event['description'] = curr_event_descr + '\n--DONE--'
    updated_event = service.events().update(calendarId=CAL_ID, eventId=event['id'], body=event).execute()
    print('\trun event for %s seconds...'%duration)
    logStatus('\trun event for %s seconds...'%duration)

    #managing physical IO PINs
    if re.search('.*GPIO*',event.get('summary','No Summary')):
      print('\tGPIO event')
      logStatus('\tGPIO event')
      res=event['summary'].split('-')
      gpio=res[1]
      op=res[2]
      print('\IO Id %s . operation %s'%(gpio,op))
      logStatus('\IO Id %s . operation %s'%(gpio,op))
      if  op.upper() == 'ON':
        GPIO.output(int(gpio), GPIO.LOW)
        time.sleep(duration)
        GPIO.output(int(gpio), GPIO.HIGH)
      else:
        GPIO.output(int(gpio), GPIO.HIGH)
        time.sleep(duration)
        GPIO.output(int(gpio), GPIO.LOW)







def todayEvent(event,currdate):
  #check if event is scheduled for current day
  res = False
  dateStart = event.get('start').get('date','NODATE')
  dateTimeStart = event.get('start').get('dateTime','NOTIME')
  #print ('Date Start: %s'%dateStart)
  #print ('Time Start: %s'%dateTimeStart)

  if dateTimeStart != 'NOTIME':
    #print ('valid Start Time found: %s'%dateTimeStart)
    if dateTimeStart.split('T')[0] == currdate: return True

  if dateStart != 'NODATE':
    #print ('valid start Date found %s'%dateStart)
    if dateStart == currdate: return True

  return res
  
  
def manageEvent(event):
  #manage Event scheduled for current day
  if event.get('start').get('dateTime','NOTIME') == 'NOTIME':
    #the event is a full day event
    runEvent(event,86400)
  else:# the event is scheduled for a particular start time and duration
    #check if we have to run it (based on starttime comparation)
    ts = time.strptime(event.get('start').get('dateTime').split('+')[0], '%Y-%m-%dT%H:%M:%S')
    te = time.strptime(event.get('end').get('dateTime').split('+')[0], '%Y-%m-%dT%H:%M:%S')
    duration = time.mktime(te)-time.mktime(ts)
    lt = time.localtime()
    if lt.tm_hour == ts.tm_hour and time.mktime(ts) <= time.mktime(lt) and time.mktime(te) > time.mktime(lt):
      runEvent(event,duration)

      #for i in range(lt.tm_min-1,lt.tm_min):
      #  if ts.tm_min == i:
      #    runEvent(event,duration)
      #    break
        #else:
          #print('scheduled starting minute not corresponding, skipping event ...')
        
    #else:
      #print('scheduled starting hour not corresponding, skipping event ...')
  
  


def myloop():
  #print('\n\n\nGetting Calendar event list...\n')
  try:

      # The Calendar API's events().list method returns paginated results, so we
      # have to execute the request in a paging loop. First, build the
      # request object. The arguments provided are:
      #   primary calendar for user
      currdate=time.strftime('%Y-%m-%d')# get current date
      # Getting Event list starting from current day
      request = service.events().list(calendarId=CAL_ID,timeMin=currdate+'T00:00:00Z')
      # Loop until all pages have been processed.
      while request != None:
        # Get the next page.
        response = request.execute()
        # Accessing the response like a dict object with an 'items' key
        # returns a list of item objects (events).
        print('\nCurrent time: %s'%time.strftime('%Y-%m-%dT%H:%M'))
        logStatus('')
        for event in response.get('items', []):
          # The event object is a dict object with a 'summary' key.
          #print ('\nEvent Summary : %s\n'%repr(event.get('summary', 'NO SUMMARY')))

          if todayEvent(event,currdate): 
            manageEvent(event)
          #else:
            #print('NOT Today Event, skipping ...')
          #print ('Start Time: %s \n'%repr(event.get('start','NO DATE').get('dateTime')))
          #print ('End Time at: %s \n'%repr(event.get('end','NO DATE').get('dateTime')))
          
        # Get the next request object by passing the previous request object to
        # the list_next method.
        request = service.events().list_next(request, response)

  except AccessTokenRefreshError:
    # The AccessTokenRefreshError exception is raised if the credentials
    # have been revoked by the user or they have expired.
    print ('The credentials have been revoked or expired, please re-run'
             'the application to re-authorize')
    logError ('The credentials have been revoked or expired, please re-run'
             'the application to re-authorize')


def loopRequest():
  #print('looping...')
  myloop()



  

if __name__ == '__main__':
  #loopRequest()
  scheduler = BackgroundScheduler(standalone=True)
  scheduler.add_job(loopRequest, 'interval', seconds=60, id='loopRequest_id',max_instances=8)
  scheduler.start() #runs the program indefinatly on an interval of 1 minutes
  print('Start main loop polling request... ( 1 minute interval)')
  print('Press Ctrl+{0} to exit'.format('Break' if os.name == 'nt' else 'C'))
  logStatus('Start main loop polling request... ( 1 minute interval)')
  try:    
    # This is here to simulate application activity (which keeps the main thread alive).
    while True:
      time.sleep(2)
  except (KeyboardInterrupt, SystemExit):
      # Not strictly necessary if daemonic mode is enabled but should be done if possible
      scheduler.shutdown()
      GPIO.cleanup()
      print ("Good bye!")
      logStatus ("Good bye!")
      
