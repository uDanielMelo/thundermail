import os
import requests
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

SCOPES = [
    'https://www.googleapis.com/auth/analytics.readonly',
    'https://www.googleapis.com/auth/youtube.readonly',
    'https://www.googleapis.com/auth/yt-analytics.readonly',
    'openid',
    'https://www.googleapis.com/auth/userinfo.email',
]


def get_flow():
    return Flow.from_client_config(
        {
            "web": {
                "client_id": os.getenv('GOOGLE_CLIENT_ID'),
                "client_secret": os.getenv('GOOGLE_CLIENT_SECRET'),
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [os.getenv('GOOGLE_REDIRECT_URI')],
            }
        },
        scopes=SCOPES,
        redirect_uri=os.getenv('GOOGLE_REDIRECT_URI'),
    )


def get_credentials_from_integration(integration):
    creds = Credentials(
        token=integration.access_token,
        refresh_token=integration.refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.getenv('GOOGLE_CLIENT_ID'),
        client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
    )
    # Renova o token se expirado
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        integration.access_token = creds.token
        integration.save(update_fields=['access_token'])
    return creds


def get_analytics_metrics(integration, days=30):
    try:
        property_id = integration.metadata.get('property_id')
        if not property_id:
            return None

        credentials = get_credentials_from_integration(integration)

        # Garante token válido
        if not credentials.token:
            return None

        url = f"https://analyticsdata.googleapis.com/v1beta/properties/{property_id}:runReport"

        payload = {
            "dateRanges": [{"startDate": f"{days}daysAgo", "endDate": "today"}],
            "metrics": [
                {"name": "sessions"},
                {"name": "activeUsers"},
                {"name": "screenPageViews"},
                {"name": "bounceRate"},
            ],
        }

        headers = {
            "Authorization": f"Bearer {credentials.token}",
            "Content-Type": "application/json",
        }

        response = requests.post(url, json=payload, headers=headers, timeout=10)

        if response.status_code != 200:
            print(f"GA API erro {response.status_code}: {response.text}")
            return None

        data = response.json()
        rows = data.get('rows', [])

        if not rows:
            return {
                'sessions': 0,
                'users': 0,
                'pageviews': 0,
                'bounce_rate': 0,
            }

        row = rows[0]['metricValues']
        return {
            'sessions': int(row[0]['value']),
            'users': int(row[1]['value']),
            'pageviews': int(row[2]['value']),
            'bounce_rate': round(float(row[3]['value']) * 100, 1),
        }

    except Exception as e:
        print(f"Erro Google Analytics: {e}")
        return None