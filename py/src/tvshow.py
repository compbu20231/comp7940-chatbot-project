import requests
from bs4 import BeautifulSoup
import random
import logging

global tvResponse

def get_tv_information():
    url = 'https://www.netflix.com/hk-en/browse/genre/83'
    global tvResponse
    if 'tvResponse' not in globals() or tvResponse is None:
        tvResponse = requests.get(url)
    soup = BeautifulSoup(tvResponse.content, 'html.parser')
    shows = []
    for review in soup.find_all(class_='nm-content-horizontal-row-item'):
        title = review.find(class_='nm-collections-title-name').text
        link = review.find('a', class_='nm-collections-link')
        if link is not None and hasattr(link, "href"):
            shows.append({'title': title, 'link': link["href"]})

    randomShows = random.sample(shows, min(5, len(shows)))
    return randomShows


def get_tv_review(url):
    logging.info('get_tv_review url = "%s"', url)
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    try:
        image = soup.find(class_='hero-image')['style'].split('"')[1]
    except:
        image = None
    
    try:
        review = soup.find(class_='title-info-synopsis').text
    except:
        review = 'review not found'

    try:
        title = soup.find('h1').text
    except:
        title = 'title not found'
    
    return {'review': review, 'image': image, 'link': url, 'title': title}