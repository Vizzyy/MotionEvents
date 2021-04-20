# Motion Events Service

Simple service that checks its source directory for incoming frames (images in jpg) from a motion activated camera. The script takes these images, sorts them, bundles them, and converts them into GIF format to be stored in a Mysql db for further consumption and review via a web interface.

```commandline
Apr 20 13:56:17 python3[364085]: Starting program...
Apr 20 14:11:17 python3[364085]: There are 53 images to parse.
Apr 20 14:11:17 python3[364085]: Bundling events...
Apr 20 14:11:20 python3[364085]: Finished rendering event0.gif in 0:00:02.669486.
Apr 20 14:11:20 python3[364085]: Successfully inserted event #0 [2021-04-20-14:10:04-event0, size: 2.89MB] into database
Apr 20 14:11:20 python3[364085]: Sleeping for 5 minute(s)...
Apr 20 14:26:20 python3[364085]: There are 64 images to parse.
Apr 20 14:26:20 python3[364085]: Bundling events...
Apr 20 14:26:23 python3[364085]: Finished rendering event0.gif in 0:00:03.071107.
Apr 20 14:26:23 python3[364085]: Successfully inserted event #0 [2021-04-20-14:22:26-event0, size: 3.49MB] into database
Apr 20 14:26:23 python3[364085]: Sleeping for 5 minute(s)...
Apr 20 14:46:24 python3[364085]: There are 124 images to parse.
Apr 20 14:46:24 python3[364085]: Bundling events...
Apr 20 14:46:32 python3[364085]: Finished rendering event0.gif in 0:00:08.769579.
Apr 20 14:46:33 python3[364085]: Successfully inserted event #0 [2021-04-20-14:45:31-event0, size: 7.16MB] into database
Apr 20 14:46:33 python3[364085]: Sleeping for 5 minute(s)...
Apr 20 14:51:33 python3[364085]: There are 50 images to parse.
Apr 20 14:51:33 python3[364085]: Bundling events...
Apr 20 14:51:36 python3[364085]: Finished rendering event0.gif in 0:00:02.780777.
Apr 20 14:51:36 python3[364085]: Successfully inserted event #0 [2021-04-20-14:50:35-event0, size: 2.84MB] into database
Apr 20 14:51:36 python3[364085]: Sleeping for 5 minute(s)...
Apr 20 14:56:36 python3[364085]: There are 546 images to parse.
Apr 20 14:56:36 python3[364085]: Bundling events...
Apr 20 14:56:42 python3[364085]: Finished rendering event0.gif in 0:00:06.439324.
Apr 20 14:56:49 python3[364085]: Finished rendering event1.gif in 0:00:06.555126.
Apr 20 14:56:56 python3[364085]: Finished rendering event2.gif in 0:00:07.014100.
Apr 20 14:57:00 python3[364085]: Finished rendering event3.gif in 0:00:04.387883.
Apr 20 14:57:01 python3[364085]: Successfully inserted event #0 [2021-04-20-14:53:38-event0, size: 7.41MB] into database
Apr 20 14:57:01 python3[364085]: Successfully inserted event #1 [2021-04-20-14:53:47-event1, size: 8.57MB] into database
Apr 20 14:57:02 python3[364085]: Successfully inserted event #2 [2021-04-20-14:53:54-event2, size: 8.89MB] into database
Apr 20 14:57:02 python3[364085]: Successfully inserted event #3 [2021-04-20-14:54:01-event3, size: 5.18MB] into database
Apr 20 14:57:02 python3[364085]: Sleeping for 5 minute(s)...
```