import os
import sys
import time
import glob
import smtplib
import datetime
import mysql.connector
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
sys.path.append(os.path.abspath("properties.py"))
from properties import *

scriptDir = '/home/barney/photos/'

while True:
	try:
		server = smtplib.SMTP('smtp.gmail.com', 587)
		server.starttls()
		server.login(getAddr(), getEmailPass())
		db = mysql.connector.connect(user='motion', password=getDbPass(), host='dinkleberg', database='motion')
		cursor = db.cursor()
	except Exception as e:
		time.sleep(5);
		print('{}\n'.format(e))
		continue

	print('\n{} -- Indexing images...'.format(str(datetime.datetime.now().strftime("%Y-%m-%d-%H:%M:%S"))))
	fullList = glob.glob(scriptDir+'*.jpg') # Get all the jpg in the directory
	print('There are {} images to parse.'.format(len(fullList)))
	list.sort(fullList, key=lambda x: int(x.split('-')[2].split('.jpg')[0]))
	# 20190122-21162100.jpg -> 21162100 -- this is comparable
	# 21:16:21-00 <- this 00 is the frame # if mult. per second

	events = []
	previousEvent = 0
	eventCount = 0
	firstEvent = True

	print('Sorting images by event...')
	# Calculate # of events
	for line in fullList:
		eventNumber = int(line.split('/')[4].split('-')[0]) # isolate just the first 2 digits of filename

		if previousEvent != eventNumber:
			previousEvent = eventNumber
			eventCount = eventCount + 1

		try:
			events[eventCount-1].append(line)
		except Exception as e:
			events.append([line])

	for event in range(eventCount): # iterate through events, event = integer
		print('\n	Creating directory: event{}'.format(event))
		os.system('mkdir {}event{}'.format(scriptDir, event)) # make a temp directory for each event

		for file in events[event]: # move files into appropriate directory - file = absolute path to file
			os.system('mv {} {}event{}/'.format(file, scriptDir, event))

		gifName = 'event{}.gif'.format(event)
		#convert -loop 0 -layers optimize -resize 400 *.jpg output2.gif
		print('	Generating gif: {}'.format(gifName))
		os.system('convert -loop 0 -layers optimize -resize 400 {}event{}/*.jpg {}'.format(scriptDir, event, gifName))
		print('	Gif complete.')
		os.system('rm -R {}event{}'.format(scriptDir, event))
		print('	Removed temp directory.')

	try:
		gifList = glob.glob(scriptDir+'*.gif')
	except Exception as e:
		gifList = []
		print('{}\n'.format(e))

	if len(gifList) > 0:
		timeStamp = str(datetime.datetime.now().strftime("%Y-%m-%d-%H:%M:%S"))
		print('Result directory: event{}'.format(timeStamp))
		os.system('mkdir {}event{}'.format(scriptDir, timeStamp)) # make a directory for this cycle
		gifCounter = 0
		for file in gifList:
			# Attach image to email
			attachment = open(file, "rb")  # file is absolute path
			msg = MIMEMultipart()
			msg.attach(MIMEText("Motion Event: \n", 'plain'))
			msg['From'] = getAddr()
			msg['To'] = getAddr()
			msg['Subject'] = "Motion Triggered"
			part = MIMEBase('application', 'octet-stream')
			part.set_payload(attachment.read())
			encoders.encode_base64(part)
			part.add_header('Content-Disposition', "attachment; filename= %s" % str('event'+str(gifCounter)+'.gif'))
			msg.attach(part)
			server.sendmail(getAddr(), getAddr(), msg.as_string())

			blob_value = open(file, 'rb').read()
			sql = 'INSERT INTO images(Time, Image) VALUES(%s, %s)'
			args = (str(timeStamp+'-'+file.split('/')[4].split('.gif')[0]), blob_value)
			cursor.execute(sql, args)
			db.commit()

			os.system('mv {} {}event{}/'.format(file, scriptDir, timeStamp)) # finally move into storage
			gifCounter = gifCounter + 1


	print('{} -- Sleeping for five minutes...\n'.format(str(datetime.datetime.now().strftime("%Y-%m-%d-%H:%M:%S"))))
	server.quit()
	time.sleep(5*60) # sleep five minutes