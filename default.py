import xbmcplugin
import xbmcgui
import xbmcaddon
import sys
import urllib, urllib2
import re
import pprint
import urlparse
import urlresolver

thisPlugin = int(sys.argv[1])
baseLink = "http://cbtv.circuit-board.de/"

_regex_extractShows = re.compile("<li class=\"page_item page-item-.*?\"><a href=\"("+baseLink+"\?page_id=.*?)\" title=\".*?\"><img src=\"("+baseLink+"wp-content/uploads/icons/.*?)\" class=\"page_icon\" alt=\".*?\">(.*?)</a></li>");
_regex_extractEpisodes = re.compile("<li><span class=\"class1\"><a href=\"("+baseLink+"\?p=.*?)\">(.*?)</a></span></li>")
_regex_extractEpisodeYouTubeId = re.compile("http://www.youtube.com/(embed|v)/(.*?)(\"|\?)")
_regex_extractEpisodeBlipTv = re.compile("(http://blip.tv/play/.*?)(.html|\")");
_regex_extractEpisodeDaylimotion = re.compile("(http://www.dailymotion.com/video/.*?)_");
_regex_extractEpisodeDescription = re.compile("<div class=\"post\">.*?<div class=\"container-header-light-normal\"><span></span></div>.*?<div class=\"copy clearfix\">(.*?)</div>.*?<div class=\"container-footer-light-normal\"><span></span></div>.*?</div>",re.DOTALL)

#blip.tv
_regex_extractVideoFeedURL = re.compile("file=(.*?)&", re.DOTALL);
_regex_extractVideoFeedURL2 = re.compile("file=(.*)", re.DOTALL);

def mainPage():
    page = load_page(baseLink)
    
    for show in _regex_extractShows.finditer(page):
        menu_link = show.group(1)
        pic = show.group(2)
        menu_name = remove_html_special_chars(show.group(3))
        addDirectoryItem(menu_name, {"action" : "show", "link": menu_link})
    xbmcplugin.endOfDirectory(thisPlugin)

def showPage(link):
    page = load_page(urllib.unquote(link))
    
    for episode in _regex_extractEpisodes.finditer(page):
        episode_link = episode.group(1)
        episode_title = remove_html_special_chars(episode.group(2))
        
        addDirectoryItem(episode_title, {"action" : "episode", "link": episode_link}, None, False)
    xbmcplugin.endOfDirectory(thisPlugin)
    
def showEpisode(link):
    episode_page = load_page(urllib.unquote(link))
    episodeDescription = _regex_extractEpisodeDescription.search(episode_page).group(1)

    videoItem = _regex_extractEpisodeYouTubeId.search(episode_page)
    if videoItem is not None:
        youTubeId = videoItem.group(2)
        showEpisodeYoutube(youTubeId)
    else:
        videoItem = _regex_extractEpisodeBlipTv.search(episode_page)
        if videoItem is not None:
            videoLink = videoItem.group(1)
            showEpisodeBip(videoLink)
        else:
            videoItem = _regex_extractEpisodeDaylimotion.search(episode_page)
            if videoItem is not None:
                videoLink = videoItem.group(1)
                showEpisodeDaylimotion(videoLink)
            else:#Fehler
                videoLink = videoItem.group(1)

def showEpisodeBip(url):    
    #GET the 301 redirect URL
    req = urllib2.Request(url)
    response = urllib2.urlopen(req)
    fullURL = response.geturl()
    
    feedURL = _regex_extractVideoFeedURL.search(fullURL)
    if feedURL is None:
        feedURL = _regex_extractVideoFeedURL2.search(fullURL)
    feedURL = urllib.unquote(feedURL.group(1))
    
    blipId = feedURL[feedURL.rfind("/")+1:]
    
    stream_url = "plugin://plugin.video.bliptv/?action=play_video&videoid=" + blipId
    item = xbmcgui.ListItem(path=stream_url)
    return xbmcplugin.setResolvedUrl(thisPlugin, True, item)

def showEpisodeYoutube(youtubeID):
    stream_url = "plugin://plugin.video.youtube/?action=play_video&videoid=" + youtubeID
    item = xbmcgui.ListItem(path=stream_url)
    xbmcplugin.setResolvedUrl(thisPlugin, True, item)
    return False
                    
def showEpisodeDaylimotion(url):
    stream_url = urlresolver.resolve(url)
    item = xbmcgui.ListItem(path=stream_url)
    xbmcplugin.setResolvedUrl(thisPlugin, True, item)
    return False

def load_page(url):
    print url
    req = urllib2.Request(url)
    response = urllib2.urlopen(req)
    link=response.read()
    response.close()
    return link

def addDirectoryItem(name, parameters={}, pic="", folder=True):
    li = xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=pic)
    if not folder:
        li.setProperty('IsPlayable', 'true')
    url = sys.argv[0] + '?' + urllib.urlencode(parameters)
    return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=li, isFolder=folder)

def remove_html_special_chars(input):
    input = input.replace("&#8211;","-")
    input = input.replace("&#8217;","'")#\x92
    input = input.replace("&#039;",chr(39))# '
    input = input.replace("&#038;",chr(38))# &
    input = input.replace("&amp;",chr(38))# &
    
    return input
    
def get_params():
    param=[]
    paramstring=sys.argv[2]
    if len(paramstring)>=2:
        params=sys.argv[2]
        cleanedparams=params.replace('?','')
        if (params[len(params)-1]=='/'):
            params=params[0:len(params)-2]
        pairsofparams=cleanedparams.split('&')
        param={}
        for i in range(len(pairsofparams)):
            splitparams={}
            splitparams=pairsofparams[i].split('=')
            if (len(splitparams))==2:
                param[splitparams[0]]=splitparams[1]
                                
    return param
    
if not sys.argv[2]:
    mainPage()
else:
    params=get_params()
    if params['action'] == "show":
        showPage(params['link'])
    elif params['action'] == "episode":
        showEpisode(params['link'])
    else:
        mainPage()
