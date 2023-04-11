import requests
from bs4 import BeautifulSoup
import random

global hikingResponse

def get_hiking_information():
    url = 'https://www.unsplash.com/search/photos/hiking-hong-kong'
    global hikingResponse
    if 'hikingResponse' not in globals() or hikingResponse is None:
        hikingResponse = requests.get(url)
    soup = BeautifulSoup(hikingResponse.content, 'html.parser')

    locations = []
    locationSubArray = []
    for location_tag in soup.find_all('div', class_='VZRk3'):
        location_ahref = location_tag.findChildren("a" , recursive=False)
        for loc in location_ahref:
            locationSubArray.append(loc.text)
        locations.append(locationSubArray)
        locationSubArray = []

    randomLocations = random.sample(locations, min(3, len(locations)))

    photoIndexs = []
    for r in randomLocations:
        photoIndexs.append(locations.index(r))

    photos = []
    for photo_tag in soup.find_all('img', class_='tB6UZ'):
        photos.append(photo_tag['src'])

    randomPhotos = []
    for p in photoIndexs:
        randomPhotos.append(photos[p])

    return [randomLocations, randomPhotos]

