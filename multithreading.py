#!/usr/bin/python
# -*- coding: utf-8 -*-

import queue
import threading
import requests
import json
import pprint
import random
import time
import urllib.request
from PIL import Image
import configparser
from datetime import datetime
import get_releases

exitFlag = 0

class my_thread (threading.Thread):
    def __init__(self, threadID, name, q):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.q = q
    def run(self):
        print ("Starting " + self.name)
        process_data(self.name, self.q)
        print ("Exiting " + self.name)
        
def process_data(threadName, q):
    while not exitFlag:
        elapsed = 0
        queueLock.acquire()
        if not workQueue.empty():
            data = q.get()
            queueLock.release()
            start_time = datetime.now()
            
            try:
                r = requests.get(url.format(data), headers = {'User-Agent': 'GetReleases/0.1'})
                if r.status_code == 200:
                    release = get_releases.get_release_info(json.loads(r.text))
                    if release[0]:
                        releases.append(release[1])
                    
                elif r.status_code == 429:
                    print("Too Many Requests!")
                    time.sleep(60)
            except Exception as err:
                print(err)
            elapsed = datetime.now() - start_time
            elapsed = elapsed.total_seconds()
        else:
            queueLock.release()
        if elapsed < 2:
            time.sleep(2 - elapsed)

# Read settings from file
config = configparser.ConfigParser()
config.read('config.ini')
token = str(config['Main']['key'])
releaseID = int(config['Settings']['starting_id'])
            
url = 'http://api.discogs.com/releases/{0}?token=' + token
thread_list = ["Thread-1", "Thread-2", "Thread-3", "Thread-4", "Thread-5", "Thread-6", "Thread-7", "Thread-8"]
queueLock = threading.Lock()
worksPerPass = 24
workQueue = queue.Queue(worksPerPass)
threads = []
threadID = 1

records = []
with open("records.txt") as file:
    records = file.readlines()
    
print (len(records))

current_index = 0
    
# Create new threads
for thread_name in thread_list:
    thread = my_thread(threadID, thread_name, workQueue)
    thread.start()
    threads.append(thread)
    threadID += 1

while True:
    # Fill the queue
    queueLock.acquire() 
    
    max_index = current_index + worksPerPass
    
    if current_index + worksPerPass > len(records):
        max_index = len(records)
    
    for x in range(current_index, max_index):
        workQueue.put(records[x])
    queueLock.release()

    releases = []
    
    # Wait for queue to empty
    while not workQueue.empty():
        pass
    print("{0}: Work queue has processed {1}-{2}, found {3} releases".format(datetime.now(), current_index, max_index, len(releases)))
    
    # Save releases to file
    if len(releases) > 0:
        get_releases.write_to_file(releases, "releases.json")
    
    current_index += worksPerPass + 1
# Notify threads it's time to exit
exitFlag = 1

# Wait for all threads to complete
for t in threads:
    t.join()
print("Exiting main Thread")