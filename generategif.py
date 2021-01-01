import datetime
import glob
import logging
import os
import sys
import time
import mysql.connector
from properties import *
from mysql.connector.constants import ClientFlag

scriptDir = getLogDir()
depth = getDepth()
sleepPeriod = getSleepPeriod()
logger = logging.getLogger('Photos')

logger.setLevel(logging.DEBUG)
# create file handler which logs even debug messages
fh = logging.FileHandler(scriptDir + 'output.log')
# create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)

# add the handlers to the logger
logger.addHandler(fh)
logger.setLevel(logging.DEBUG)

sys.path.append(os.path.abspath("properties.py"))

ssl_config = {
    'user': 'motion',
    'password': getDbPass(),
    'host': getDbHost(),
    'port': 9004,
    'database': 'motion',
    'client_flags': [ClientFlag.SSL],
    'ssl_ca': ssl_path,
    'use_pure': True
}


def log_msq(msg: str):
    print(msg)
    logger.info(msg)


print("\n\nStarting up program...")
logger.info("\n\nStarting up program...")
while True:
    try:
        db = mysql.connector.connect(**ssl_config)
        cursor = db.cursor()
        print("connected to resources")
    except Exception as e:
        logger.info(f'{e}')
        time.sleep(5)
        continue

    # logger.info('Checking for images...')
    fullList = glob.glob(scriptDir + '*.jpg')  # Get all the jpg in the directory

    if (len(fullList)) > 0:
        log_msq(f'There are {len(fullList)} images to parse.')
        list.sort(fullList, key=lambda x: int(x.split('-')[2].split('.jpg')[0]))
        # 20190122-21162100.jpg -> 21162100 -- this is comparable
        # 21:16:21-00 <- this 00 is the frame # if mult. per second
        # example image output 01-20200118-18332317.jpg

        events = []
        previousEvent = 0
        eventCount = 0

        log_msq('Sorting images by event...')
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
            log_msq(f'Creating directory: event{event}')
            os.system(f'mkdir {scriptDir}event{event}')  # make a temp directory for each event

            for file in events[event]:  # move files into appropriate directory - file = absolute path to file
                os.system(f'mv {file} {scriptDir}event{event}/')

            gifName = 'event{}.gif'.format(event)
            # convert -loop 0 -layers optimize -resize 400 *.jpg output2.gif
            log_msq(f'Generating gif: {gifName}')
            os.system(f'convert -loop 0 -layers optimize -resize 400 {scriptDir}event{event}/*.jpg {scriptDir}{gifName}')
            log_msq('Gif complete.')
            os.system(f'rm -rf {scriptDir}event{event}')
            log_msq('Removed temp directory.')
        try:
            gifList = glob.glob(scriptDir + '*.gif')
            log_msq(gifList)
        except Exception as e:
            gifList = []
            log_msq(f'{e}')

        if len(gifList) > 0:
            timeStamp = str(datetime.datetime.now().strftime("%Y-%m-%d-%H:%M:%S"))
            log_msq(f'Result directory: event{timeStamp}')
            os.system(f'mkdir {scriptDir}event{timeStamp}')  # make a directory for this cycle
            gifCounter = 0
            for file in gifList:
                try:
                    original_datetime = events[gifCounter][0].split('/')[depth].split('.')[0][:-2]
                    # original_datetime example: 01-20200118-18331700
                    formatted_original_datetime = datetime.datetime\
                        .strptime(original_datetime[3:], '%Y%m%d-%H%M%S')\
                        .strftime('%Y-%m-%d-%H:%M:%S')

                    log_msq(f"Event originally occurred: {formatted_original_datetime}")
                    blob_value = open(file, 'rb').read()
                    sql = 'INSERT INTO images(Time, Image) VALUES(%s, %s)'
                    args = (str(formatted_original_datetime + '-' + file.split('/')[depth].split('.gif')[0]), blob_value)
                    cursor.execute(sql, args)
                    db.commit()
                    log_msq(f'Successfully inserted event #{str(gifCounter)} ({args[0]}) into database')
                except Exception as e:
                    log_msq(f'Error: {e}')
                os.system(f'mv {file} {scriptDir}event{timeStamp}/')  # finally move into storage
                gifCounter = gifCounter + 1

    log_msq(f'Sleeping for {sleepPeriod} minutes...')
    time.sleep(sleepPeriod * 60)  # sleep five minutes
