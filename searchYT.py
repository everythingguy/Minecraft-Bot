import bs4, requests, sys, urllib, simplejson

def search(searchText, playlist=False):
    results = []
    query = requests.get("https://www.youtube.com/results?search_query=" + searchText).text
    soup = bs4.BeautifulSoup(query, features="html.parser")

    div = [d for d in soup.find_all('div') if d.has_attr('class') and 'yt-lockup-dismissable' in d['class']]

    for d in div:
        img0 = d.find_all('img')[0]
        a0 = d.find_all('a')[0]
        imgL = img0['src'] if not img0.has_attr('data-thumb') else img0['data-thumb']
        a0 = [x for x in d.find_all('a') if x.has_attr('title')][0]
        result = (imgL, 'http://www.youtube.com/'+a0['href'], a0['title'])
        if '&list=' in result[1] and playlist == False:
            pass
        else:
            results.append(result)

    return results

def getPlaylist(url):
    videos = []
    
    listId = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)['list'][0]
    url = 'https://www.youtube.com/playlist?list=' + listId

    html = requests.get(url).text
    soup = bs4.BeautifulSoup(html, features='html.parser')

    trs = soup.find_all('tr', attrs={'class': 'pl-video yt-uix-tile '})

    for tr in trs:
        link = 'https://www.youtube.com/watch?v=' + tr['data-video-id']
        video = [tr['data-title'], link]
        if video[0] != "[Deleted video]" and video[0] != "[Private video]":
            videos.append(video)

    #print(trs[0])
    return videos

def getInfo(link):
    query = requests.get(link).text
    soup = bs4.BeautifulSoup(query, features="html.parser")

    div = soup.find_all("title")[0].text
    div = div.replace(" - YouTube", "")
    return str(div)

