import random
import os
from googleapiclient.discovery import build
import html


global cookResponse
def get_cooking_video_information():
    api_key = os.environ['YOUTUBE_API_KEY'] # Replace with your YouTube API key
    youtube = build('youtube', 'v3', developerKey=api_key)
    videos = []
    request = youtube.search().list(
            part='id,snippet',
            channelId="UCIEv3lZ_tNXHzL3ox-_uUGQ",
            maxResults=50,
            type='video' )
    global cookResponse
    if 'cookResponse' not in globals() or cookResponse is None:
        cookResponse = request.execute()

    for item in cookResponse['items']:
        video = {
            'title': html.unescape(item['snippet']['title']),
            'link': "<a href='https://www.youtube.com/watch?v={}'>{}</a>".format(item['id']['videoId'], html.unescape(item['snippet']['description'])),
            'image': item['snippet']['thumbnails']['default']['url']
        }
        videos.append(video)

    randomVideos = random.sample(videos, min(5, len(videos)))
    return randomVideos
