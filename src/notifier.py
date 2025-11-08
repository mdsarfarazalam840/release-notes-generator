import os
import requests
from src.utils import env

def notify_slack(message: str, webhook: str = None):
    webhook = webhook or env('SLACK_WEBHOOK')
    if not webhook:
        print('No webhook specified')
        return
    resp = requests.post(webhook, json={'text': message})
    resp.raise_for_status()
    return resp
