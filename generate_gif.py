import datetime
import glob
import os
import shutil
import time
import boto3
import mysql.connector
from properties import *
from mysql.connector.constants import ClientFlag

# In order to set a soft limit on how large a gif can be, we limit the amount of frames that go into a gif.
# 150 = 9.2MB ish, 100 = 6.1MB ish, etc, but encoding will add ~36% additional size w/ current parameters
event_size_limit = 1000
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
s3_client = boto3.client('s3')

print("Starting program...")

while True:
    try:
        # Start with DB connection so that we don't attempt to process and risk manipulating/losing data
        db = mysql.connector.connect(**ssl_config)
        cursor = db.cursor()
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
        event_num = int(full_list[0][0:2])
        for file_path in full_list:
            # Check if the bundle is under limit, and the event number is still the same
            # Regardless of the current count, separate events should always bundle separately
            if len(events[-1]) < event_size_limit and int(file_path[0:2]) == event_num:
                events[-1].append(file_path)
            else:
                event_num = int(file_path[0:2])
                events.append([file_path])

        [print(f"{events.index(event)}: {len(event)}") for event in events]

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
            for gif in gif_list:
                try:
                    # "events" is an array of arrays of frames pulled during motion event, it looks something like this:
                    # [['202-20210723-13374304.jpg', '202-20210723-13374305.jpg', ... '202-20210723-13374919.jpg'],
                    # ['203-20210723-13374304.jpg', '203-20210723-13374305.jpg', ... '203-20210723-13374919.jpg']]
                    # The event number, 202 in the above example, is reset maybe on reboot of service, or system?
                    # We grab the first frame of each event as our key for "original_datetime", this represents when
                    # that event occurred.
                    # print(events[gif_list.index(gif)])
                    original_datetime = events[gif_list.index(gif)][0]  # Grab the first frame of the event
                    print(f"First frame of event: {original_datetime}")
                    original_datetime = original_datetime.split('.')[0].split('-')  # Strip whatever file extension
                    # original_datetime = original_datetime.split('-')  # split ['202', '20210723', '13374304']
                    original_datetime = f"{original_datetime[-2]}-{original_datetime[-1][:-2]}"  # concat: 20210723-133743
                    print(f"Parsed timeframe: {original_datetime}")

                    formatted_original_datetime = datetime.datetime\
                        .strptime(original_datetime, '%Y%m%d-%H%M%S')\
                        .strftime('%Y-%m-%d-%H:%M:%S')
                    final_time = f"{str(formatted_original_datetime)}-event{gif_list.index(gif)}"

                    # Insert blob into DB, and push to S3 for off-site backup
                    blob_value = open(gif, 'rb').read()
                    sql = 'INSERT INTO images(Time, Image) VALUES(%s, %s)'
                    args = (final_time, blob_value)
                    cursor.execute(sql, args)
                    db.commit()
                    s3_client.upload_file(gif, "vizzyy-motion-events", f"{final_time}.gif")

                    file_size = '%.2f' % float(os.path.getsize(gif) / 1000 / 1000)
                    print(f'Successfully inserted event #{str(gif_list.index(gif))} '
                          f'[{args[0]}, size: {file_size}MB] into database')

                    os.remove(gif)
                except Exception as e:
                    print(f'ERROR: {type(e).__name__} {e}')

        db.close()
        cursor.close()
        print(f'Sleeping for {sleep_minutes} minute(s)...')

    time.sleep(sleep_minutes * 60)
