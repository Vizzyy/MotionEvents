import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import mysql.connector
import sys
from PIL import Image
from io import StringIO
import os
sys.path.append(os.path.abspath("/home/pi/sensitiveParameters.py"))
from sensitiveParameters import *

chunkSize = 100
body = sys.argv[1]

with open('/home/pi/listOfImages.txt', 'r') as f:
	fullList = f.read().splitlines()

print(str(len(fullList)) + " files in list.")

def split(arr, size):
	arrs = []
	while len(arr) > size:
		pice = arr[:size]
		arrs.append(pice)
		arr = arr[size:]
	arrs.append(arr)
	return arrs

chunks = split(fullList, chunkSize)
print("Given chunk size of:" + str(chunkSize) + ", there are " + str(len(chunks)) + " chunks.")

db = mysql.connector.connect(user='motion', password=getDbPass(), host='dinkleberg', database='motion')
sIO = StringIO()

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
				filename = 'frame' + str(counter) + '.jpg'
				# print("Opening file: " + line)
				attachment = open(line, "rb")  # line is absolute path to file
				part = MIMEBase('application', 'octet-stream')
				part.set_payload(attachment.read())
				encoders.encode_base64(part)
				part.add_header('Content-Disposition', "attachment; filename= %s" % filename)
				msg.attach(part)
				imagePath = line
				image = Image.open(imagePath)
				blob_value = open(imagePath, 'rb').read()
				# print("Inserting into DB: " + line)
				sql = 'INSERT INTO images(Time, Image) VALUES(%s, %s)'
				args = (imagePath[-19:], blob_value)
				cursor = db.cursor()
				cursor.execute(sql, args)
				print("Finished with: " + line)
				counter = counter + 1
			except Exception as e:
				print("Exception with file: " + line)
				print(str(e))

		if counter > 0:  # If we have photos accumulated, email them
			server = smtplib.SMTP('smtp.gmail.com', 587)
			server.starttls()
			server.login(getAddr(), getEmailPass())
			text = msg.as_string()
			print("Attempting to send Email size: "+str(len(text))+" -- " + str(chunkCounter) + "/" + str(len(chunks)))
			print("")
			server.sendmail(fromaddr, toaddr, text)
			server.quit()

			db.commit()

	except Exception as e:
		print("Failed to process chunk #: " + str(chunkCounter))
		print(str(e))
		db.rollback()
	chunkCounter = chunkCounter + 1

deleteCounter = 0
for line in fullList:
	try:
		os.remove(line)
		deleteCounter = deleteCounter + 1
		print("Removed file #" + str(deleteCounter) + ": " + line)
	except:
		print("Could not remove file: " + line)

f = open('/home/pi/listOfImages.txt', 'w')  # erase contents last
print("Clearing list.")
f.close()
db.close()
