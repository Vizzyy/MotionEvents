import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import mysql.connector
import sys
from PIL import Image
import os
sys.path.append(os.path.abspath("/home/pi/properties.py"))
from properties import *

chunkSize = 100
body = sys.argv[1]

with open('/home/pi/listOfImages.txt', 'r') as f:
	fullList = f.read().splitlines()

newLine = "\n"
totalLog = ""
print(str(len(fullList)) + " file(s) in list.")
total = totalLog + str(len(fullList)) + " file(s) in list."+newLine

def split(arr, size):
	arrs = []
	while len(arr) > size:
		pice = arr[:size]
		arrs.append(pice)
		arr = arr[size:]
	arrs.append(arr)
	return arrs

chunks = split(fullList, chunkSize)
print("Given chunk size of: " + str(chunkSize) + ", there is/are " + str(len(chunks)) + " chunk(s).")
totalLog = totalLog + "Given chunk size of: " + str(chunkSize) + ", there is/are " + str(len(chunks)) + " chunk(s)." + newLine

db = mysql.connector.connect(user='motion', password=getDbPass(), host='dinkleberg', database='motion')

server = smtplib.SMTP('smtp.gmail.com', 587)
server.starttls()
server.login(getAddr(), getEmailPass())

chunkCounter = 1
for chunk in chunks:
	counter = 0
	msg = MIMEMultipart()
	msg.attach(MIMEText(body, 'plain'))
	msg['From'] = getAddr()
	msg['To'] = getAddr()
	msg['Subject'] = "Motion Triggered"

	try:
		for line in chunk:  # Parse through list of images and attach them to email and Insert to DB
			try:
				# Open image
				filename = 'frame' + str(counter) + '.jpg'
				attachment = open(line, "rb")  # line is absolute path to file

				# Attach image to email
				part = MIMEBase('application', 'octet-stream')
				part.set_payload(attachment.read())
				encoders.encode_base64(part)
				part.add_header('Content-Disposition', "attachment; filename= %s" % filename)
				msg.attach(part)

				# Also insert into DB
				imagePath = line
				image = Image.open(imagePath)
				blob_value = open(imagePath, 'rb').read()
				sql = 'INSERT INTO images(Time, Image) VALUES(%s, %s)'
				args = (imagePath[-19:], blob_value)
				cursor = db.cursor()
				cursor.execute(sql, args)

				print("Finished attaching image and inserting blob: " + line)
				totalLog = totalLog + "Finished attaching image and inserting blob: " + line + newLine
				counter = counter + 1
			except Exception as e:
				print("Exception with file: " + line)
				print(str(e))
				totalLog = totalLog + "Exception with file: " + line + newLine + str(e) + newLine

		if counter > 0:  # If we have photos accumulated, email them
			text = msg.as_string()
			print("Attempting to send Email size: "+str(len(text))+" -- " + str(chunkCounter) + "/" + str(len(chunks)))
			totalLog = totalLog + "Attempting to send Email size: "+str(len(text))+" -- " + str(chunkCounter) + "/" + str(len(chunks)) + newLine
			server.sendmail(getAddr(), getAddr(), text)
			print("		SUCCESS")
			totalLog = totalLog + "		SUCCESS" + newLine
			db.commit() # Commit to DB when email is sent

	except Exception as e:
		print("Failed to process chunk #: " + str(chunkCounter))
		print(str(e))
		totalLog = totalLog + "Failed to process chunk #: " + str(chunkCounter) + newLine + str(e) + newLine
		db.rollback() # Roll back if exception, so that we don't end up with duplicates

	chunkCounter = chunkCounter + 1

deleteCounter = 0
for line in fullList:
	try:
		os.remove(line)
		deleteCounter = deleteCounter + 1
		print("Removed file #" + str(deleteCounter) + ": " + line)
		totalLog = totalLog + "Removed file #" + str(deleteCounter) + ": " + line + newLine
	except Exception as e:
		print("Could not remove file: " + line)
		print(str(e))
		totalLog = totalLog + "Could not remove file: " + line + newLine + str(e) + newLine

try:
	totalLog = totalLog + "Emailing log of event..."
	# One last email for logs
	msg = MIMEMultipart()
	msg.attach(MIMEText(totalLog, 'plain'))
	msg['From'] = getAddr()
	msg['To'] = getAddr()
	msg['Subject'] = "Email Event Log"
	server.sendmail(getAddr(), getAddr(), msg.as_string())
	print("Email log success!")
except Exception as e:
	print("Could not send log: ")
	print(str(e))

f = open('/home/pi/listOfImages.txt', 'w')  # erase contents last
print("Clearing list.")
f.close()
server.quit()
db.close()
print("Cleanup Complete.")
