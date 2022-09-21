"""Addon Implementation"""
from urllib.error import HTTPError
from urllib.parse import urlparse
from urllib.parse import urlunparse
import xbmc
import xbmcaddon
import requests


def check_mopidy_state():
    host = addon.getSettingString("mopidy_host")
    url = urlunparse(urlparse(f"http://{host}/mopidy/rpc"))

    try:
        response = requests.post(
            url=url,
            json={"jsonrpc": "2.0", "id": 1, "method": "core.playback.get_state"}
        )
        response.raise_for_status()
        result = response.json()
        if result['result'] != "playing":
            return False
        return True
    except HTTPError:
        xbmc.log("Http request failed -> assuming no playback",
                 level=xbmc.LOGDEBUG)
        return False


if __name__ == '__main__':
    monitor = xbmc.Monitor()
    addon = xbmcaddon.Addon()
    max_retries = addon.getSettingInt("fail_count")
    cur_retries = 0
    saved_state = xbmc.getCondVisibility("System.IdleShutdownInhibited")

    while not monitor.abortRequested():
        if monitor.waitForAbort(addon.getSettingInt("check_interval")):
            break
        xbmc.log("Running checks", level=xbmc.LOGDEBUG)
        if cur_retries == 0:
            saved_state = xbmc.getCondVisibility("System.IdleShutdownInhibited")

        if check_mopidy_state():
            cur_retries = 0
        else:
            cur_retries += 1

        if cur_retries >= max_retries:
            xbmc.log("Max fail checks reached -> stop inhibiting suspend",
                     level=xbmc.LOGDEBUG)
            cur_retries = 0
            xbmc.executebuiltin(f"InhibitIdleShutdown({str(saved_state).lower()})")
        else:
            xbmc.executebuiltin('InhibitIdleShutdown(true)')
        xbmc.log("Done with checks -> waiting", level=xbmc.LOGDEBUG)
