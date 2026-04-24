import csv
import sys
import requests
from datetime import timedelta
from collections import OrderedDict

INSTANCES = [
    'https://invidious.fdn.fr',
    'https://yewtu.be',
    'https://vid.puffyan.us',
    'https://invidious.projectsegfau.lt',
    'https://invidious.slipfox.xyz',
    'https://invidious.privacydev.net',
    'https://iv.ggtyler.dev',
    'https://invidious.lunar.icu'
]

SOURCES = {
    'channel': [
        'UCGEaIQSwlHRoG5gtg_MvWYw',
        'UCQQbm4mH_9RtUiYoKr1Gq7g'
    ],
    'playlist': [
        'PLdwaQvROfx1cbUWaSsD3G8_JKHRozr5rD'
    ]
}

OUTPUT_FILE = 'youtube_videos.csv'

def get_working_instance():
    for instance in INSTANCES:
        try:
            resp = requests.get(f'{instance}/api/v1/trending', timeout=10)
            if resp.status_code == 200:
                print(f'Using instance: {instance}')
                return instance
        except Exception:
            continue
    print('Error: No Invidious instance available.')
    sys.exit(1)

def fetch_channel_videos(instance, channel_id):
    videos = []
    url = f'{instance}/api/v1/channels/{channel_id}/videos'
    params = {'sort_by': 'newest'}
    
    while True:
        try:
            resp = requests.get(url, params=params, timeout=30)
            if resp.status_code != 200:
                print(f'Error fetching channel {channel_id}: HTTP {resp.status_code}')
                break
            data = resp.json()
        except Exception as e:
            print(f'Error fetching channel {channel_id}: {e}')
            break
        
        for video in data.get('videos', []):
            video_id = video.get('videoId')
            if not video_id:
                continue
            title = video.get('title', '')
            author = video.get('author', '')
            length_sec = video.get('lengthSeconds', 0)
            length_str = str(timedelta(seconds=length_sec))
            video_url = f'https://www.youtube.com/watch?v={video_id}'
            videos.append({
                'video_name': title,
                'channel_name': author,
                'length': length_str,
                'video_url': video_url
            })
        
        continuation = data.get('continuation')
        if not continuation:
            break
        params['continuation'] = continuation
    
    return videos

def fetch_playlist_videos(instance, playlist_id):
    videos = []
    url = f'{instance}/api/v1/playlists/{playlist_id}'
    params = {}
    
    while True:
        try:
            resp = requests.get(url, params=params, timeout=30)
            if resp.status_code != 200:
                print(f'Error fetching playlist {playlist_id}: HTTP {resp.status_code}')
                break
            data = resp.json()
        except Exception as e:
            print(f'Error fetching playlist {playlist_id}: {e}')
            break
        
        for video in data.get('videos', []):
            video_id = video.get('videoId')
            if not video_id:
                continue
            title = video.get('title', '')
            author = video.get('author', '')
            length_sec = video.get('lengthSeconds', 0)
            length_str = str(timedelta(seconds=length_sec))
            video_url = f'https://www.youtube.com/watch?v={video_id}'
            videos.append({
                'video_name': title,
                'channel_name': author,
                'length': length_str,
                'video_url': video_url
            })
        
        continuation = data.get('continuation')
        if not continuation:
            break
        params['continuation'] = continuation
    
    return videos

def main():
    instance = get_working_instance()
    all_videos = OrderedDict()
    
    for channel_id in SOURCES['channel']:
        print(f'Fetching channel: {channel_id}')
        videos = fetch_channel_videos(instance, channel_id)
        for v in videos:
            key = v['video_url']
            if key not in all_videos:
                all_videos[key] = v
        print(f'Fetched {len(videos)} videos')
    
    for playlist_id in SOURCES['playlist']:
        print(f'Fetching playlist: {playlist_id}')
        videos = fetch_playlist_videos(instance, playlist_id)
        for v in videos:
            key = v['video_url']
            if key not in all_videos:
                all_videos[key] = v
        print(f'Fetched {len(videos)} videos')
    
    print(f'Total unique videos: {len(all_videos)}')
    
    with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=['video_name', 'channel_name', 'length', 'video_url'])
        writer.writeheader()
        for v in all_videos.values():
            writer.writerow(v)
    
    print(f'Saved to {OUTPUT_FILE}')

if __name__ == '__main__':
    main()
