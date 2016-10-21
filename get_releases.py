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
        return True
    else:
        return False

def write_to_file(releases):
    print('Writing releases to file...')
    with open(save_file) as file:
        data = json.load(file)
    # Update the current file with the new releases
    for release in releases:
        data.append(release)
    with open(save_file, 'w') as f:
        json.dump(data, f, indent = 4)
    
def get_track_list(tracklist):
    tracks = []
    for track_info in tracklist:
        track = {}
        add_attribute('title', 'title', track_info, track)
        add_attribute('position', 'position', track_info, track)
        add_attribute('duration', 'duration', track_info, track)
        tracks.append(track)
    return tracks

def get_genres(genres):
    list = []
    for genre in genres:
        list.append(genre)
    return list
    
def get_artists(artists):
    list = []
    for artist in artists:
        list.append(artist['name'])
    return list
    
def check_if_vinyl(formats):
    if len(formats) == 0:
        return False
        
    format = formats[0]
    
    if 'descriptions' not in format:
        return False
        
    if 'Album' not in format['descriptions']:
        return False
    
    if format['name'] != 'Vinyl':
        return False
    
    return True
    
def convert_image(path):
    image = Image.open(path)
    print(image.format, image.size, image.mode)
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
            
def get_images(images, release_id):
    save_file = 'img/{0}.jpg'.format(release_id)
    for image in images:
        if image['type'] == 'primary':
            width = image['width']
            height = image['height']
            # If the ratio is a perfect square
            if width >= 500 and height >= 500 and width / height == 1.0:
                urllib.request.urlretrieve(image['resource_url'], save_file)
                convert_image(save_file)
                return True
    return False

def get_release_info(data):
    release = {}
    print ('Release ID: {0}'.format(data['id']), end=' | ')
    
    if not check_if_vinyl(data['formats']):
        print('The record is not a vinyl record')
        return (False, release)
    if not add_attribute('title', 'title', data, release):
        print('No title was found')
        return (False, release)
    if not add_attribute('country', 'country', data, release):
        print('No release country was found')
        return (False, release)
    if not add_attribute('released', 'year', data, release):
        print('No release year was found')
        return (False, release)
    # Convert year to int
    release['year'] = get_num(release['year'])
    print (release['year'])

    # Artist(s)
    if 'artists' in data:
        release['artists'] = get_artists(data['artists'])
    else:
        print ('Artist(s) were not found in release')
        return (False, release)
    # Genres
    if 'genres' in data:
        release['genres'] = get_genres(data['genres'])
    else:
        print('Genre(s) were not found in release')
        return (False, release)
    # Tracklist
    if 'tracklist' in data:
        release['tracklist'] = get_track_list(data['tracklist'])
    else:
        print('Tracklist was not found in release')
        return (False, release)
    # Images
    if 'images' in data:
        if get_images(data['images'], data['id']):
            release['path'] = data['id']
        else:
            print('No image atleast 500x500 was found')
            return (False, release)
    else:
        print('No images were found')
        return (False, release)
    # If everything was sucessfully got, return release
    return (True, release)

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
    
    while True:
        old_amount = amount
        # Poor man's throttle
        time.sleep(0.25)
        
        release = (False, {})
        
        try:
            release = get_release(release_id, settings)
        except HTTPError:
            print("Error happened")
        
        # Check if we're supposed to write current releases to file
        update = amount % 10 == 0 and amount != 0 and old_amount != amount
        add = release != None and release[0]

        if add:
            print ("Found suitable release! " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            releases.append(release[1])
            accepted_releases.add(release_id)
            amount += 1
        if update:
            write_to_file(releases)
            # Reset releases
            releases = []
        release_id += 1
# Script Start
settings = read_settings()
get_releases(settings)