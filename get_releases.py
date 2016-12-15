#!/usr/bin/python
# -*- coding: utf-8 -*-
import requests
import json
import pprint
import random
import time
import urllib.request
import os
from PIL import Image
from datetime import datetime
from pymongo import MongoClient

pp = pprint.PrettyPrinter(indent = 4)

client = MongoClient()
db = client.albums
collection = db.releases

def add_attribute(attribute, save_attribute, data, release):
    if attribute in data:
        release[save_attribute] = data[attribute]
    else:
        raise Exception('Attribute {0} not found in release'.format(attribute))

def write_to_file(releases, save_file):
    print('Writing releases to file...')
    data = {}
    data["records"] = []
    # Check if file exists
    # If it does, load the existing data
    if os.path.exists(save_file) and os.stat(save_file).st_size != 0:
        with open(save_file, 'r') as file:
            data = json.load(file)
    # Update the current file with the new releases
    for release in releases:
        data["records"].append(release)
    with open(save_file, 'w+') as f:
        json.dump(data, f, indent = 4)
        
def save_to_database(releases):
    collection.insert_many(releases)
    
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
                size = (image['width'], image['height'])
                if size[0] >= 500 and size[0] / size[1] == 1:
                    urllib.request.urlretrieve(image['resource_url'], save_file)
                    convert_image(save_file)
                    print("Image {0} was found!".format(data['id']))
                    return
    raise Exception('No images were found')

def get_release_info(data):
    release = {}
    try:
        check_if_vinyl(data)
        add_attribute('id', 'id', data, release)
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
    except Exception as err:
        return (False, release)
    else:
        return (True, release) 