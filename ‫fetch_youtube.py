import os
import csv
import sys
import yt_dlp
from collections import OrderedDict

# لینک‌هایی که می‌خواهید ویدیوهایشان استخراج شود
SOURCES = [
    'https://www.youtube.com/channel/UCGEaIQSwlHRoG5gtg_MvWYw',
    'https://www.youtube.com/channel/UCQQbm4mH_9RtUiYoKr1Gq7g',
    'https://www.youtube.com/playlist?list=PLdwaQvROfx1cbUWaSsD3G8_JKHRozr5rD',
]

OUTPUT_CSV = 'youtube_videos.csv'

# تنظیمات yt-dlp برای استخراج متادیتا (بدون دانلود محتوا)
EXTRACT_OPTS = {
    'quiet': True,
    'no_warnings': True,
    'extract_flat': True,        # فقط لینک‌ها را می‌گیرد، وارد تکی‌تکی نمی‌شود
    'force_generic_extractor': False,
    'ignoreerrors': True,
    'dump_single_json': False,
    'playlistend': None,         # None یعنی همه
}

# تنظیمات برای دانلود ویدیو
DOWNLOAD_OPTS = {
    'quiet': True,
    'no_warnings': True,
    'format': 'bestvideo[height<=720]+bestaudio/best[height<=720]',  # حداکثر 720p تا حجم معقول بماند
    'merge_output_format': 'mp4',
    'outtmpl': 'downloads/%(title).100s [%(id)s].%(ext)s',  # نام فایل
    'ignoreerrors': True,
    'max_downloads': 3,          # تعداد ویدیو از هر منبع
    'playlistend': 3,            # فقط ۳ ویدیوی آخر (جدیدترین‌ها) 
}

def ensure_downloads_dir():
    os.makedirs('downloads', exist_ok=True)

def fetch_metadata(url):
    """اطلاعات تمام ویدیوهای یک کانال/پلی‌لیست را برمی‌گرداند."""
    opts = EXTRACT_OPTS.copy()
    # اضافه کردن یک extractor مناسب
    with yt_dlp.YoutubeDL(opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
        except Exception as e:
            print(f'Error extracting {url}: {e}', file=sys.stderr)
            return []

    entries = []
    if 'entries' in info:  # پلی‌لیست/کانال
        for entry in info['entries']:
            if entry is None:
                continue
            video_id = entry.get('id')
            if not video_id:
                # برخی موارد ممکن است id نداشته باشند (مثلاً لینک‌های پاک‌شده)
                continue
            title = entry.get('title', '')
            channel = entry.get('channel', '') or entry.get('uploader', '')
            duration = entry.get('duration')  # ثانیه یا None
            if duration:
                hrs, remainder = divmod(int(duration), 3600)
                mins, secs = divmod(remainder, 60)
                length_str = f'{hrs}:{mins:02d}:{secs:02d}' if hrs else f'{mins}:{secs:02d}'
            else:
                length_str = ''
            video_url = f'https://www.youtube.com/watch?v={video_id}'
            entries.append({
                'video_name': title,
                'channel_name': channel,
                'length': length_str,
                'video_url': video_url,
                'id': video_id
            })
    else:  # یک ویدیوی تنها
        video_id = info.get('id')
        if video_id:
            title = info.get('title', '')
            channel = info.get('channel', '') or info.get('uploader', '')
            duration = info.get('duration')
            if duration:
                hrs, rem = divmod(int(duration), 3600)
                mins, secs = divmod(rem, 60)
                length_str = f'{hrs}:{mins:02d}:{secs:02d}' if hrs else f'{mins}:{secs:02d}'
            else:
                length_str = ''
            video_url = f'https://www.youtube.com/watch?v={video_id}'
            entries.append({
                'video_name': title,
                'channel_name': channel,
                'length': length_str,
                'video_url': video_url,
                'id': video_id
            })
    return entries

def download_videos(source_url, max_videos=3):
    """چند ویدیو از یک منبع دانلود کرده و لیست فایل‌های دانلود شده را برمی‌گرداند."""
    opts = DOWNLOAD_OPTS.copy()
    opts['playlistend'] = max_videos
    opts['max_downloads'] = max_videos
    opts['outtmpl'] = 'downloads/%(title).100s [%(id)s].%(ext)s'
    ensure_downloads_dir()
    with yt_dlp.YoutubeDL(opts) as ydl:
        try:
            ydl.download([source_url])
        except Exception as e:
            print(f'Download error from {source_url}: {e}', file=sys.stderr)

def main():
    all_videos = OrderedDict()  # استفاده از OrderedDict برای حذف تکراری بر اساس video_url
    for src in SOURCES:
        print(f'Fetching metadata from: {src}')
        entries = fetch_metadata(src)
        for e in entries:
            key = e['video_url']
            if key not in all_videos:
                all_videos[key] = e
    print(f'Total unique videos: {len(all_videos)}')

    # ذخیره CSV
    with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=['video_name', 'channel_name', 'length', 'video_url'])
        writer.writeheader()
        for v in all_videos.values():
            writer.writerow({
                'video_name': v['video_name'],
                'channel_name': v['channel_name'],
                'length': v['length'],
                'video_url': v['video_url']
            })
    print(f'Saved {OUTPUT_CSV}')

    # دانلود چند ویدیو از هر منبع
    print('Downloading a few sample videos (3 from each source)...')
    for src in SOURCES:
        download_videos(src, max_videos=3)
    print('Downloads complete.')

if __name__ == '__main__':
    main()
