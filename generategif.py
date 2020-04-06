import os
import sys
import time
import glob
import smtplib
import datetime
import logging
import mysql.connector
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

from properties import getAddr, getEmailPass, getDbPass, getLogDir, getDbHost, getDepth, getSleepPeriod

scriptDir = getLogDir()
depth = getDepth()
sleepPeriod = getSleepPeriod()
# create logger with 'spam_application'
logger = logging.getLogger('output')
logger.setLevel(logging.DEBUG)
# create file handler which logs even debug messages
fh = logging.FileHandler(scriptDir + 'output.log')
fh.setLevel(logging.DEBUG)
# create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
# add the handlers to the logger
logger.addHandler(fh)

sys.path.append(os.path.abspath("properties.py"))
print("\n\nStarting up program...")
logger.info("\n\nStarting up program...")
while True:
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(getAddr(), getEmailPass())
        db = mysql.connector.connect(user='motion', password=getDbPass(), host=getDbHost(), port=9004,
                                     database='motion')
        cursor = db.cursor()
    except Exception as e:
        try:
            server.quit()
        except Exception as b:
            logger.info('{}'.format(b))
        logger.info('{}'.format(e))
        time.sleep(5)
        continue

    # logger.info('Checking for images...')
    fullList = glob.glob(scriptDir + '*.jpg')  # Get all the jpg in the directory

    if (len(fullList)) > 0:
        logger.info('There are {} images to parse.'.format(len(fullList)))
        print('There are {} images to parse.'.format(len(fullList)))
        list.sort(fullList, key=lambda x: int(x.split('-')[2].split('.jpg')[0]))
        # 20190122-21162100.jpg -> 21162100 -- this is comparable
        # 21:16:21-00 <- this 00 is the frame # if mult. per second
        # example image output 01-20200118-18332317.jpg

        events = []
        previousEvent = 0
        eventCount = 0
        firstEvent = True

        logger.info('Sorting images by event...')
        print('Sorting images by event...')
        # Calculate # of events
        for line in fullList:
            eventNumber = int(line.split('/')[depth].split('-')[0])  # isolate just the first 2 digits of filename

            if previousEvent != eventNumber:
                previousEvent = eventNumber
                eventCount = eventCount + 1

            try:
                events[eventCount - 1].append(line)
            except Exception as e:
                events.append([line])

        for event in range(eventCount):  # iterate through events, event = integer
            logger.info('Creating directory: event{}'.format(event))
            print('Creating directory: event{}'.format(event))
            os.system('mkdir {}event{}'.format(scriptDir, event))  # make a temp directory for each event

            for file in events[event]:  # move files into appropriate directory - file = absolute path to file
                os.system('mv {} {}event{}/'.format(file, scriptDir, event))

            gifName = 'event{}.gif'.format(event)
            # convert -loop 0 -layers optimize -resize 400 *.jpg output2.gif
            logger.info('   Generating gif: {}'.format(gifName))
            print('Generating gif: {}'.format(gifName))
            os.system('convert -loop 0 -layers optimize -resize 400 {}event{}/*.jpg {}{}'.format(scriptDir, event, scriptDir, gifName))
            logger.info('   Gif complete.')
            print('Gif complete.')
            os.system('rm -R {}event{}'.format(scriptDir, event))
            logger.info('   Removed temp directory.')
            print('Removed temp directory.')
        try:
            gifList = glob.glob(scriptDir + '*.gif')
            print(gifList)
            logger.info(gifList)
        except Exception as e:
            gifList = []
            logger.info('{}'.format(e))

        if len(gifList) > 0:
            timeStamp = str(datetime.datetime.now().strftime("%Y-%m-%d-%H:%M:%S"))
            logger.info('Result directory: event{}'.format(timeStamp))
            print('Result directory: event{}'.format(timeStamp))
            os.system('mkdir {}event{}'.format(scriptDir, timeStamp))  # make a directory for this cycle
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
                part.add_header('Content-Disposition', "attachment; filename= %s" % str('event' + str(gifCounter) + '.gif'))
                msg.attach(part)
                try:
                    server.sendmail(getAddr(), getAddr(),
                                    msg.as_string())  # Send mail -- Can be too large so must catch exception
                    logger.info('Successfully emailed event #{}.'.format(str(gifCounter)))
                    print('Successfully emailed event #{}.'.format(str(gifCounter)))
                    blob_value = open(file, 'rb').read()
                    sql = 'INSERT INTO images(Time, Image) VALUES(%s, %s)'
                    args = (str(timeStamp + '-' + file.split('/')[depth].split('.gif')[0]), blob_value)
                    cursor.execute(sql, args)
                    db.commit()
                    logger.info('Successfully inserted event #{} into database.'.format(str(gifCounter)))
                    print('Successfully inserted event #{} into database.'.format(str(gifCounter)))
                except Exception as e:
                    logger.info('{}'.format(e))

                os.system('mv {} {}event{}/'.format(file, scriptDir, timeStamp))  # finally move into storage
                gifCounter = gifCounter + 1

    # logger.info('Sleeping for five minutes...')
    print('Sleeping for {} minutes...'.format(sleepPeriod))
    server.quit()
    time.sleep(sleepPeriod * 60)  # sleep five minutes
