import os
import requests
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from datetime import date, timedelta


def get_credentials(integration):
    creds = Credentials(
        token=integration.access_token,
        refresh_token=integration.refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.getenv('GOOGLE_CLIENT_ID'),
        client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
    )
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        integration.access_token = creds.token
        integration.save(update_fields=['access_token'])
    return creds


def get_youtube_metrics(integration):
    try:
        creds = get_credentials(integration)
        headers = {"Authorization": f"Bearer {creds.token}"}

        # Canal
        channel_resp = requests.get(
            "https://www.googleapis.com/youtube/v3/channels",
            headers=headers,
            params={"part": "snippet,statistics", "mine": "true"},
            timeout=10
        )

        if channel_resp.status_code != 200:
            print(f"YouTube canal erro {channel_resp.status_code}: {channel_resp.text}")
            return None

        items = channel_resp.json().get('items', [])
        if not items:
            return None

        channel = items[0]
        stats = channel['statistics']
        channel_id = channel['id']

        # Últimos 5 vídeos
        search_resp = requests.get(
            "https://www.googleapis.com/youtube/v3/search",
            headers=headers,
            params={
                "part": "snippet",
                "forMine": "true",
                "type": "video",
                "order": "date",
                "maxResults": 5,
            },
            timeout=10
        )

        recent_videos = []
        if search_resp.status_code == 200:
            video_items = search_resp.json().get('items', [])
            video_ids = [v['id']['videoId'] for v in video_items]

            # Busca estatísticas de cada vídeo
            if video_ids:
                stats_resp = requests.get(
                    "https://www.googleapis.com/youtube/v3/videos",
                    headers=headers,
                    params={
                        "part": "snippet,statistics",
                        "id": ",".join(video_ids),
                    },
                    timeout=10
                )

                if stats_resp.status_code == 200:
                    for v in stats_resp.json().get('items', []):
                        vs = v.get('statistics', {})
                        recent_videos.append({
                            'title': v['snippet']['title'],
                            'published_at': v['snippet']['publishedAt'][:10],
                            'thumbnail': v['snippet']['thumbnails']['default']['url'],
                            'video_id': v['id'],
                            'views': int(vs.get('viewCount', 0)),
                            'likes': int(vs.get('likeCount', 0)),
                            'comments': int(vs.get('commentCount', 0)),
                        })

        # YouTube Analytics — últimos 30 dias
        analytics_metrics = None
        end_date = date.today().strftime('%Y-%m-%d')
        start_date = (date.today() - timedelta(days=30)).strftime('%Y-%m-%d')

        analytics_resp = requests.get(
            "https://youtubeanalytics.googleapis.com/v2/reports",
            headers=headers,
            params={
                "ids": f"channel=={channel_id}",
                "startDate": start_date,
                "endDate": end_date,
                "metrics": "views,estimatedMinutesWatched,averageViewDuration,subscribersGained,subscribersLost,impressions,impressionClickThroughRate",
                "dimensions": "",
            },
            timeout=10
        )

        if analytics_resp.status_code == 200:
            rows = analytics_resp.json().get('rows', [])
            if rows:
                r = rows[0]
                analytics_metrics = {
                    'views_30d': int(r[0]),
                    'watch_time_30d': int(r[1]),
                    'avg_view_duration': int(r[2]),
                    'subscribers_gained': int(r[3]),
                    'subscribers_lost': int(r[4]),
                    'impressions': int(r[5]),
                    'ctr': round(float(r[6]) * 100, 2),
                }
        else:
            print(f"YouTube Analytics erro {analytics_resp.status_code}: {analytics_resp.text}")

        return {
            'channel_name': channel['snippet'].get('title', ''),
            'channel_id': channel_id,
            'subscribers': int(stats.get('subscriberCount', 0)),
            'total_views': int(stats.get('viewCount', 0)),
            'total_videos': int(stats.get('videoCount', 0)),
            'recent_videos': recent_videos,
            'analytics': analytics_metrics,
        }

    except Exception as e:
        print(f"Erro YouTube: {e}")
        return None