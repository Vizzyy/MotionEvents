import datetime
import glob
import os
import shutil
import time
import mysql.connector
from properties import *
from mysql.connector.constants import ClientFlag

# In order set a soft limit on how large a gif can be, we limit the amount of frames that go into a gif.
# The goal is to keep the gif size <= 10MB. This limit will need to be changed depending on frame size/quality.
event_size_limit = 150
sleep_minutes = 5
if os.environ.get('DB_HOST'):
    DB_HOST = os.environ.get('DB_HOST')
ssl_config = {
    'user': 'motion',
    'password': DB_PASS,
    'host': DB_HOST,
    'port': DB_PORT,
    'database': DB_SCHEMA,
    'client_flags': [ClientFlag.SSL],
    'ssl_ca': SSL_PATH,
    'use_pure': True
}


while True:
    try:
        # Start with DB connection so that we don't attempt to process and risk manipulating/losing data
        db = mysql.connector.connect(**ssl_config)
        cursor = db.cursor()
        print("DB connection secured, beginning processing...")
    except Exception as e:
        print(f'ERROR: Failed to connect to DB: {e}')
        time.sleep(5)
        continue

    full_list = glob.glob('*.jpg')  # Get all the jpg in the directory

    if (len(full_list)) > 0:
        print(f'There are {len(full_list)} images to parse.')

        # 01-20190122-21162100.jpg -> 21162100 -- this is comparable
        # 21:16:21-00 <- this 00 is the frame-number if multiple frames per second
        list.sort(full_list, key=lambda x: int(x.split('-')[2].split('.jpg')[0]))

        events = [[]]

        print('Bundling events...')
        for file_path in full_list:
            if len(events[-1]) < event_size_limit:
                events[-1].append(file_path)
            else:
                events.append([file_path])

        event_counter = 0
        for event in events:
            processing_start_time = datetime.datetime.now()
            event_name = f"event{event_counter}"
            gif_name = f'{event_name}.gif'

            # Make temp directory for frames in event
            if not os.path.isdir(event_name):
                os.mkdir(event_name)

            # Move our frames there
            for frame in event:
                shutil.move(frame, event_name)

            # Use https://imagemagick.org/index.php to create optimized gif
            os.system(f'convert -loop 0 -layers optimize -resize 400 {event_name}/*.jpg {gif_name}')

            # Recursively remove directory
            shutil.rmtree(event_name)

            print(f"Finished rendering {gif_name} in {datetime.datetime.now() - processing_start_time}.")
            event_counter += 1

        try:
            gif_list = glob.glob('*.gif')
            list.sort(gif_list)
        except Exception as e:
            gif_list = []
            print(f'ERROR: Somehow no Gif created? {e}')

        if len(gif_list) > 0:
            gif_count = 0
            for gif in gif_list:
                try:
                    # original_datetime output example: 20190122-211621 (removed first 3, and last 2, digits)
                    original_datetime = events[gif_count][0].split('/')[-1].split('.')[0][3:-2]
                    formatted_original_datetime = datetime.datetime\
                        .strptime(original_datetime, '%Y%m%d-%H%M%S')\
                        .strftime('%Y-%m-%d-%H:%M:%S')

                    # Insert blob into DB
                    blob_value = open(gif, 'rb').read()
                    sql = 'INSERT INTO images(Time, Image) VALUES(%s, %s)'
                    args = (f"{str(formatted_original_datetime)}-event{gif_count}", blob_value)
                    cursor.execute(sql, args)
                    db.commit()

                    file_size = '%.2f' % float(os.path.getsize(gif) / 1000 / 1000)
                    print(f'Successfully inserted event #{str(gif_count)} '
                          f'[{args[0]}, size: {file_size}MB] into database')

                    os.remove(gif)
                except Exception as e:
                    print(f'ERROR: {e}')
                gif_count = gif_count + 1

        db.close()
        cursor.close()

    print(f'Sleeping for {sleep_minutes} minute(s)...')
    time.sleep(sleep_minutes * 60)  # sleep five minutes
