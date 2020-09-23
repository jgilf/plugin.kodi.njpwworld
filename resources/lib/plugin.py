# -*- coding: utf-8 -*-

import logging
import routing
import sys
import xbmcaddon
from resources.lib import api
from resources.lib import kodiutils
from resources.lib import kodilogging
from xbmcgui import ListItem
from xbmcplugin import (
    addDirectoryItem,
    addSortMethod,
    endOfDirectory,
    setResolvedUrl)


ADDON = xbmcaddon.Addon()
logger = logging.getLogger(ADDON.getAddonInfo('id'))
kodilogging.config()
plugin = routing.Plugin()


@plugin.route('/')
def index():
    if not api.is_loggedin():
        addDirectoryItem(
            plugin.handle, plugin.url_for(login),
            ListItem(
                "Login", iconImage=ADDON.getAddonInfo('icon'),
                thumbnailImage=ADDON.getAddonInfo('icon')))
    else:
        addDirectoryItem(
            plugin.handle, plugin.url_for(show_section, "live"),
            ListItem(
                "Live", iconImage=ADDON.getAddonInfo('icon'),
                thumbnailImage=ADDON.getAddonInfo('icon')),
            True)
        addDirectoryItem(
            plugin.handle, plugin.url_for(show_section, "ondemand"),
            ListItem(
                "On Demand", iconImage=ADDON.getAddonInfo('icon'),
                thumbnailImage=ADDON.getAddonInfo('icon')),
            True)
        addDirectoryItem(
            plugin.handle, plugin.url_for(logout),
            ListItem(
                "Logout", iconImage=ADDON.getAddonInfo('icon'),
                thumbnailImage=ADDON.getAddonInfo('icon')))
    addDirectoryItem(
        plugin.handle, plugin.url_for(open_settings),
        ListItem(
            "Settings", iconImage=ADDON.getAddonInfo('icon'),
            thumbnailImage=ADDON.getAddonInfo('icon')),
        True)
    endOfDirectory(plugin.handle)


@plugin.route('/<section_id>')
def show_section(section_id):
    if section_id == 'live':
        programs = api.get_programs(
            'p/search', params={'category_code': 'l_live'})
        add_items(programs)
    if section_id == 'ondemand':
        addDirectoryItem(
            plugin.handle, plugin.url_for(show_section, "series"),
            ListItem(
                "Series", iconImage=ADDON.getAddonInfo('icon'),
                thumbnailImage=ADDON.getAddonInfo('icon')),
            True)
        addDirectoryItem(
            plugin.handle, plugin.url_for(show_section, "original"),
            ListItem(
                "Original", iconImage=ADDON.getAddonInfo('icon'),
                thumbnailImage=ADDON.getAddonInfo('icon')),
            True)
    if section_id == 'series':
        series = api.get_series()
        add_items(series)
    if section_id == 'original':
        programs = api.get_programs('p/original')
        add_groups(programs)
    endOfDirectory(plugin.handle)


@plugin.route('/series/<series_id>')
def show_series(series_id):
    programs = api.get_programs(
        'p/search', params={'category_code': series_id})
    add_groups(programs)
    endOfDirectory(plugin.handle)


@plugin.route('/group/<group_id>')
def show_group(group_id):
    programs = api.get_programs(
        'p/search', params={'program_group_code': group_id})
    add_items(programs)
    endOfDirectory(plugin.handle)


@plugin.route('/play/<media_id>')
def play(media_id):
    liz = ListItem(path=api.get_video_url(media_id))
    setResolvedUrl(int(sys.argv[1]), True, liz)
    endOfDirectory(plugin.handle)


@plugin.route('/settings')
def open_settings():
    kodiutils.show_settings()


@plugin.route('/login')
def login():
    login = api.login()
    if login:
        kodiutils.refresh()


@plugin.route('/logout')
def logout():
    logout = api.logout()
    if logout:
        kodiutils.refresh()


def add_groups(items):
    groups = set((item.group_name, item.group_code) for item in items)
    for group in groups:
        liz = ListItem(group[0], thumbnailImage=ADDON.getAddonInfo('icon'))
        liz.setInfo(
            type='Video',
            infoLabels={'sorttile': group[1]})
        addSortMethod(plugin.handle, 29)
        addDirectoryItem(plugin.handle, plugin.url_for(
            show_group, group[1]), liz, True)


def add_items(items):
    for item in items:
        if item.item_type == 'show':
            liz = ListItem(
                item.name, iconImage=item.icon,
                thumbnailImage=item.thumbnail)
            addDirectoryItem(plugin.handle, plugin.url_for(
                show_series, item.media_id), liz, True)
        elif item.item_type == 'episode':
            liz = ListItem(
                item.name, iconImage=item.icon,
                thumbnailImage=item.thumbnail)
            liz.setInfo(
                type='Video',
                infoLabels={
                    "tvshowtitle": item.show_name,
                    "title": item.title,
                    "plot": item.description,
                    "genre": item.genre,
                    "year": item.air_date[0:4],
                    "duration": item.duration,
                    "aired": item.air_date})
            liz.setProperty('IsPlayable', 'true')
            addDirectoryItem(
                plugin.handle, plugin.url_for(
                    play, item.media_id), liz)


def run():
    plugin.run()
