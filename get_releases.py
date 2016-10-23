#!/usr/bin/python
# -*- coding: utf-8 -*-

import requests
import json
import pprint
import random
import time
import urllib.request
from PIL import Image
import configparser
from datetime import datetime

pp = pprint.PrettyPrinter(indent = 4)

# Settings
def read_settings():
    config = configparser.ConfigParser()
    config.read('config.ini')
    
    settings = {}
    settings['key'] = str(config['Main']['key'])
    
    settings['save_file'] = str(config['Main']['save_file'])
    settings['starting_id'] = int(config['Settings']['starting_id'])
    
    settings['headers'] = {
        'User-Agent': str(config['Main']['user_agent'])
    }
    return settings

def add_attribute(attribute, save_attribute, data, release):
    if attribute in data:
        release[save_attribute] = data[attribute]
    else:
        raise Exception('Attribute {0} not found in release'.format(attribute))

def write_to_file(releases, save_file):
    print('Writing releases to file...')
    with open(save_file) as file:
        data = json.load(file)
    # Update the current file with the new releases
    for release in releases:
        data.append(release)
    with open(save_file, 'w+') as f:
        json.dump(data, f, indent = 4)
    
def get_track_list(data):
    if 'tracklist' not in data:
        raise Exception('Tracklist not found in data')
    tracklist = data['tracklist']
    tracks = []
    for track_info in tracklist:
        track = {}
        add_attribute('title', 'title', track_info, track)
        add_attribute('position', 'position', track_info, track)
        add_attribute('duration', 'duration', track_info, track)
        tracks.append(track)
    return tracks

def get_genres(data):
    if 'genres' not in data:
        raise Exception('Genre(s) were not found in data')
    genres = data['genres']
    list = []
    for genre in genres:
        list.append(genre)
    return list
    
def get_artists(data):
    if 'artists' not in data:
        raise Exception('Artist(s) were not found in data')
    list = []
    artists = data['artists']
    for artist in artists:
        list.append(artist['name'])
    return list
    
def check_if_vinyl(data):
    if 'formats' in data:
        formats = data['formats']
        if len(formats) >= 1:
            format = formats[0]
            if 'descriptions' in format:
                if 'Album' in format['descriptions']:
                    if format['name'] == 'Vinyl':
                        return True
    raise Exception('Release is not a record')
    
def convert_image(path):
    image = Image.open(path)
    # Convert to non progressive
    image.save(path, "PNG", progressive=False)
    
def get_num(str):
    if len(str) == 4:
        return int(str)
    numbers = []
    number = ''
    for char in str:
        if char.isdigit():
            number += char
        else:
            numbers.append(number)
            number = ''
    numbers.append(number)
    
    for number in numbers:
        number = int(number)
        if number >= 1000 and number <= 9999:
            return number
    raise Exception('No release year was found')
            
def get_images(data):
    if 'images' in data:
        images = data['images']
        save_file = 'img/{0}.jpg'.format(data['id'])
        for image in images:
            if image['type'] == 'primary':
                # If the ratio is a perfect square
                width = image['width']
                height = image['height']
                ratio = width / height
                
                if width >= 500 and height >= 500 and ratio == 1:
                    urllib.request.urlretrieve(image['resource_url'], save_file)
                    convert_image(save_file)
                    return True
    raise Exception('No images were found')

def get_release_info(data):
    release = {}
    try:
        check_if_vinyl(data)
        add_attribute('title', 'title', data, release)
        add_attribute('country', 'country', data, release)
        add_attribute('released', 'year', data, release)
        # Convert year to int
        release['year'] = get_num(release['year'])
        # Artist(s)
        release['artists'] = get_artists(data)
        # Genres
        release['genres'] = get_genres(data)
        # Tracklist
        release['tracklist'] = get_track_list(data)
        # Images
        get_images(data)
        # If everything was sucessfully got, return release
        return (True, release)
    except Exception as err:
        #exc_type, exc_value, exc_traceback = sys.exc_info()
        #traceback.print_tb(exc_traceback)
        return (False, {})

def get_release(release_id, settings):
    url = 'http://api.discogs.com/releases/{0}?token={1}'
    # Get a random release
    r = requests.get(url.format(release_id, settings['key']), headers = settings['headers'])
    if r.status_code == 200:
        j = json.loads(r.text)
        return get_release_info(j)

def get_releases(settings):
    accepted_releases = set()
    releases = []
    amount = 0
    
    release_id = settings['starting_id']
    
    failed_release = -1
    
    while True:
        # Poor man's throttle
        #time.sleep(0.25)
        release = get_release(release_id, settings)
        # Check if we're supposed to write current releases to file
        update = False

        if release != None and release[0]:
            print ("Found suitable release! " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            releases.append(release[1])
            accepted_releases.add(release_id)
            amount += 1
            if failed_release != -1:
                print("Try to print release id")
                print("Release ID {0}-{1} were not interesting".format(failed_release, release_id - 1))
                failed_release = -1
        else:
            if failed_release == -1:
                failed_release = release_id
        if update:
            write_to_file(releases, settings['save_file'])
            # Reset releases
            releases = []
        release_id += 1
# Script Start
settings = read_settings()
get_releases(settings)