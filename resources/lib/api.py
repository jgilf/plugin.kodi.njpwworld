from time import time
import requests

from resources.lib import kodiutils

API_BASE = 'https://api.njpwworld.com/ftv/v1/{}'
API_KEY = 'PWmQBbZWp6nHYXpM'
API_TOKEN = kodiutils.get_setting('api_token')
HEADERS = {
    'User-Agent': 'firetv_sdk_google_atv_x86_com.njpwworld.NJPWWORLD'
}
LANG = 2 if kodiutils.get_setting('lang') == 'English' else 1


class ListItem(object):
    def __init__(self):
        self.item_type = "episode"
        self.show_name = ""
        self.name = ""
        self.title = ""
        self.description = ""
        self.icon = ""
        self.thumbnail = ""
        self.fan_art = ""
        self.banner = ""
        self.media_id = ""
        self.air_date = ""
        self.duration = ""
        self.genre = ""
        self.on_watchlist = False


def is_loggedin():
    if kodiutils.get_setting('api_token'):
        now = time()
        expires = kodiutils.get_setting("api_token_expiry")
        if expires <= now:
            if not login():
                return
        return True


def login():
    email = kodiutils.get_setting('email')
    password = kodiutils.get_setting('password')
    if not email or not password:
        kodiutils.notification(
            'Missing Credentials',
            'Enter credentials in settings and try again', time=1000)
    r = requests.post(
        API_BASE.format('login'),
        params={
            'api_key': API_KEY
        },
        data={
            'login_id': email,
            'pw': password,
            'type': '1',
            'device_identifier': '',
        }, headers=HEADERS)
    if r.json()['status'] == 1:
        kodiutils.set_setting('api_token', r.json()['api_token'])
        kodiutils.set_setting("api_token_expiry", 60*60*24*14 + time())
        return True
    else:
        kodiutils.notification(
            'Login Failed',
            'Login failed, check credentials and try again', time=1000)


def logout():
    requests.post(
        API_BASE.format('logout'),
        params={
            'api_key': API_KEY
        },
        data={
            'api_token': API_TOKEN,
        }, headers=HEADERS)
    kodiutils.set_setting('api_token', '')
    return True


def get_series():
    r = requests.get(
        API_BASE.format('c/series'),
        params={
            'limit': 200,
            'offset': 0,
            'lang': LANG,
            'api_key': API_KEY
        }, headers=HEADERS)

    items = []

    for i in r.json()['response']:
        item = ListItem()
        item.item_type = 'show'
        item.title = i['category_name']
        item.name = i['category_name']
        item.icon = i['image_url'] + '.tif'
        item.thumbnail = i['image_url'] + '.tif'
        item.media_id = i['category_code']
        item.air_date = i.get('display_start_datetime')
        items.append(item)

    return items


def get_programs(route, params={}, limit=None):
    items = []
    params.update({
        'limit': 200,
        'offset': 0,
        'lang': LANG,
        'api_key': API_KEY
    })
    while True:
        if limit and params['offset'] >= limit:
            return items
        r = requests.get(
            API_BASE.format(route),
            params=params, headers=HEADERS)
        if not r.json().get('response'):
            return items
        items.extend(get_items(r.json()['response']))
        params['offset'] += 200


def get_items(response):
    items = []
    for i in response:
        item = ListItem()
        item.title = i['program_name']
        item.group_name = i['program_group_name']
        item.group_code = i['program_group_code']
        item.name = i['program_name']
        item.icon = i['image_url'] + '.tif'
        item.thumbnail = i['image_url'] + '.tif'
        item.media_id = i['program_code']
        item.air_date = i.get(
            'exhibition_date', i.get('display_start_datetime'))
        items.append(item)

    return items


def get_video_url(media_id):
    data = {
        'api_key': API_KEY,
        'api_token': API_TOKEN,
        'lang': LANG,
    }
    r = requests.post(
        API_BASE.format('p/detail/%s' % media_id),
        data=data,
        headers=HEADERS)

    data['video_code'] = r.json()['response']['video_code']

    r = requests.post(
        API_BASE.format('playlist'),
        data=data,
        headers=HEADERS)

    return r.json()['playlist_url']
