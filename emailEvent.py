import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import mysql.connector
import sys
import os
import datetime
import glob
sys.path.append(os.path.abspath("properties.py"))
from properties import *

body = sys.argv[1]
scriptDir = '/home/pi/'
gif_name = 'outputName.gif'
newLine = "\n"
totalLog = ""
msg = MIMEMultipart()
msg.attach(MIMEText("DB Primary Key: "+body+newLine+newLine, 'plain'))
msg['From'] = getAddr()
msg['To'] = getAddr()
msg['Subject'] = "Motion Triggered"

db = mysql.connector.connect(user='motion', password=getDbPass(), host='dinkleberg', database='motion')
cursor = db.cursor()

server = smtplib.SMTP('smtp.gmail.com', 587)
server.starttls()
server.login(getAddr(), getEmailPass())

fullList = glob.glob(scriptDir+'*.jpg') # Get all the jpg in the directory
list.sort(fullList, key=lambda x: int(x.split('-')[1].split('.jpg')[0])) # 20190122-21162100.jpg -> 21162100 -- this is comparable
print(fullList)

with open(scriptDir+'listOfImages.txt', 'w') as file:
	for item in fullList:
		file.write("%s\n" % item)

print(str(datetime.datetime.now()) + " -- " + str(len(fullList)) + " file(s) in list. ")
totalLog = totalLog + str(datetime.datetime.now()) + " -- " + str(len(fullList)) + " file(s) in list. " + newLine

if len(fullList) == 0: # Stop emailing me on restart
	raise SystemExit() # Graceful exit

filepath = scriptDir+gif_name
try:
	print(str(datetime.datetime.now()) + " -- " + "Converting event into GIF format... ")
	totalLog = totalLog + str(datetime.datetime.now()) + " -- Converting event into GIF format... " + newLine
	os.system('convert @{}listOfImages.txt {}{}'.format(scriptDir, scriptDir, gif_name))
	print(str(datetime.datetime.now()) + " -- " + "Success! Converted event into GIF format. ")
	totalLog = totalLog + str(datetime.datetime.now()) + " -- Success! Converted event into GIF format. " + newLine

	# Open image
	attachment = open(filepath, "rb")  # line is absolute path to file

	# Attach image to email
	part = MIMEBase('application', 'octet-stream')
	part.set_payload(attachment.read())
	encoders.encode_base64(part)
	part.add_header('Content-Disposition', "attachment; filename= %s" % gif_name)
	msg.attach(part)

	# Also insert into DB
	blob_value = blob_value = open(filepath, 'rb').read()
	sql = 'INSERT INTO images(Time, Image) VALUES(%s, %s)'
	args = (body, blob_value)
	cursor.execute(sql, args)
	db.commit()
	print(str(datetime.datetime.now()) + " -- " + "Commited Gif to Database. ")
	totalLog = totalLog + str(datetime.datetime.now()) + " -- Commited Gif to Database. " + newLine
except Exception as e:
	print(str(e))
	totalLog = totalLog + str(e) + newLine
	totalLog = totalLog + str(datetime.datetime.now()) + " -- Emailing event Failure... "
	msg.attach(MIMEText(totalLog, 'plain'))
	server.sendmail(getAddr(), getAddr(), msg.as_string())
	raise SystemExit()

for line in fullList:
	try:
		os.remove(line)
	except Exception as e:
		print("Could not remove file: " + line)
		print(str(e))
		totalLog = totalLog + "Could not remove file: " + line + newLine + str(e) + newLine

try:
	totalLog = totalLog + str(datetime.datetime.now()) + " -- Emailing log of event... "
	msg.attach(MIMEText(totalLog, 'plain'))
	server.sendmail(getAddr(), getAddr(), msg.as_string())
	print(str(datetime.datetime.now()) + " -- " + "Email log success!")
except Exception as e:
	print("Could not send log: ")
	print(str(e))

f = open('listOfImages.txt', 'w')  # erase contents
f.close()
os.remove(scriptDir+"outputName.gif")
print(str(datetime.datetime.now())+" -- Clearing list.")
server.quit()
print(str(datetime.datetime.now())+" -- Cleanup Complete.")
