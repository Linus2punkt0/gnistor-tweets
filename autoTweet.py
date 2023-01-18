# -*- coding: utf-8 -*-
from twython import Twython, TwythonError
from datetime import date, datetime, timedelta
from operator import itemgetter
import random, time, os, feedparser, csv, pytz
import auth
import locale

tz = pytz.timezone("Europe/Stockholm")
curTime = datetime.now(tz)
timeLimit = curTime - timedelta(hours = 1)
basePath = "/var/www/local/gnistorTweet"
logPath = "/var/www/local/logs/"
localCal = basePath + "/calendar.csv"
authFile = basePath + "/auth"
calendar = feedparser.parse("https://www.gnistor.se/feed/index.xml")
podfeed = feedparser.parse("https://www.gnistor.se/podcast/index.xml")
posts = []
queue = []



twitter = Twython(auth.APP_KEY, auth.APP_SECRET, auth.OAUTH_TOKEN, auth.OAUTH_TOKEN_SECRET)


def writeLog(message):
    now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    date = datetime.now().strftime("%y%m%d")
    message = str(now) + ": " + message + "\n"
    log = logPath + "gnistor_" + date + ".log"
    if os.path.exists(log):
        append_write = 'a'
    else:
        append_write = 'w'
    dst = open(log, append_write)
    dst.write(message)
    dst.close()

# Itterating through the feed and collecting the relevant data from all future events. Also reverses the order of the feed, to get events closer in time first.
for post in calendar.entries:
    eventTime = datetime.strptime(post.published, '%a, %d %b %Y %X %z')
    if (eventTime > curTime):
        item = {
            "title": post.title,
            "eventTime": eventTime,
            "url": post.link
        }
        posts.insert(0, item)

def getPodTweets():
    tweets = []
    for post in podfeed.entries:
        postTime = datetime.strptime(post.published, '%a, %d %b %Y %X %z')
        if (postTime > timeLimit):
            url = post.link
            title = post.title
            tweet = "Ny podd från Gnistor: " + title + "\n" + url
            tweets.append(tweet)
    if (len(tweets) > 0):
        queue.append(tweets)
    else:
        writeLog("No new podcast episodes")

def saveLocalCalendar():
    if os.path.exists(localCal):
        os.remove(localCal)
    for post in posts:
        eventTime = post["eventTime"]
        url = post["url"]
        if os.path.exists(localCal):
            append_write = 'a'
        else:
            append_write = 'w'
        dst = open(localCal, append_write, encoding='utf-8')
        dst.write(url + "," + eventTime.strftime("%Y-%m-%d %X%z") + "\n" )
        dst.close()

def getNewEvents():
    if (os.path.exists(localCal)):
        localEvents = []
        with open(localCal, 'r') as cal:
            for line in cal:
                eventArr = line.replace('\n', "").split(',')
                url = eventArr[0]
                eventTime = datetime.strptime(eventArr[1], '%Y-%m-%d %X%z')
                if (eventTime > curTime):
                    localEvents.append(url)
        if (len(localEvents) > 0):
            tweet = ""
            tweets = []
            for post in posts:
                eventTime = post["eventTime"]
                url = post["url"]
                if (eventTime > curTime and url not in localEvents):
                    title = post["title"]
                    eventInfo = eventTime.strftime("%Y-%m-%d %H:%M") + ": " + title + " " + url
                    if (len(tweet) + len(eventInfo) < 280):
                        if (len(tweet) == 0 and len(tweets) == 0):
                            tweet = "Nya event i kalendern:\n"
                        tweet += eventInfo + "\n"
                    else:
                        tweets.append(tweet)
                        tweet = "Nya event i kalendern:\n"
            if (len(tweet) > 0):
                tweets.append(tweet)
            if (len(tweets) > 0):
                queue.append(tweets)
            else:
                writeLog("No new events in the calendar")

def comingWeek():
    tweet = ""
    tweets = []
    for post in posts:
        eventTime = post["eventTime"]
        url = post["url"]
        if (eventTime.isocalendar().week == curTime.isocalendar().week + 1):
            title = post["title"]
            eventInfo = eventTime.strftime("%Y-%m-%d %H:%M") + ": " + title + ", " + url
            if (len(tweet) + len(eventInfo) < 280):
                if (len(tweet) == 0 and len(tweets) == 0):
                    tweet = "Här är kommande veckans händelser:\n"
                tweet += eventInfo + "\n"
            else:
                tweets.append(tweet)
                tweet = ""
                tweet += eventInfo + "\n"
    if (len(tweet) > 0):
        tweets.append(tweet)
    if (len(tweets) > 0):
        queue.append(tweets)
    else:
        writeLog("No events in the coming week")
    
def comingMonth():
    saved = locale._setlocale(locale.LC_TIME)
    locale.setlocale(locale.LC_TIME, 'sv_SE')
    month = curTime.strftime('%B')
    locale.setlocale(locale.LC_TIME, saved)
    tweet = ""
    tweets = []
    for post in posts:
        eventTime = post["eventTime"]
        url = post["url"]
        if (eventTime.month == curTime.month and eventTime.year == curTime.year):
            title = post["title"]
            eventInfo = eventTime.strftime("%Y-%m-%d %H:%M") + ": " + title + ", " + url
            if (len(tweet) + len(eventInfo) < 280):
                if (len(tweet) == 0 and len(tweets) == 0):
                    tweet = "Här är alla händelser i kalendern för " + month + ":\n"
                tweet += eventInfo + "\n"
            else:
                tweets.append(tweet)
                tweet = ""
                tweet += eventInfo + "\n"
    if (len(tweet) > 0):
        tweets.append(tweet)
    if (len(tweets) > 0):
        queue.append(tweets)
    else:
        writeLog("No events in the coming month")

def inTwoHours():
    tweets = []
    for post in posts:
        eventTime = post["eventTime"]
        url = post["url"]
        if (eventTime < curTime+timedelta(hours=2)):
            title = post["title"]
            tweets.append("Snart är det dags för " + title + "! \n" + url)
    if (len(tweets) > 0):
        queue.append(tweets)
    else:
        writeLog("No events coming up in the next two hours")

def todayTomorrow():
    today = ""
    todays = []
    tomorrow = ""
    tomorrows = []
    for post in posts:
        eventTime = post["eventTime"]
        url = post["url"]
        title = post["title"]
        eventInfo = eventTime.strftime("%Y-%m-%d %H:%M") + ": " + title + " " + url
        if (eventTime.date() == curTime.date()):
            if (len(today) + len(eventInfo) < 280):
                if (len(today) == 0 and len(todays) == 0):
                    today = "Missa inte dagens evenemang:\n"
                today += eventInfo + "\n"
            else:
                todays.append(today)
                today = ""
        elif (eventTime.date() == curTime.date() + timedelta(days=1)):
            if (len(tomorrow) + len(eventInfo) < 280):
                if (len(tomorrow) == 0 and len(tomorrows) == 0):
                    tomorrow = "Följande evenemang finns i kalendern för imorgon:\n"
                tomorrow += eventInfo + "\n"
            else:
                tomorrows.append(tomorrow)
                tomorrow = ""
    if (len(today) > 0):
        todays.append(today)
    if (len(tomorrow) > 0):
        tomorrows.append(tomorrow)
    tweets = todays + tomorrows
    if (len(tweets) > 0):
        queue.append(tweets)
    else:
        writeLog("No events for today or tomorrow")

def gatherPosts():
    inTwoHours()
    if (curTime.day == 1 and curTime.hour == 9):
        comingMonth()
    elif (curTime.weekday() == 6 and curTime.hour == 17):
        comingWeek()
    elif (curTime.hour == 9):
        todayTomorrow()
    getPodTweets()
    getNewEvents()
    saveLocalCalendar()

def postTweets():
    gatherPosts()
    if (len(queue) == 0):
        return
    elif (len(queue) < 6):
        waitTime = 10
    elif (len(queue) < 12):
        waitTime = 5
    else:
        waitTime = 1
    a = ""
    for section in queue:
        for tweet in section:
            if (len(a) == 0):
                a = twitter.update_status(status=tweet, auto_populate_reply_metadata=True)
            else:
                a = twitter.update_status(status=tweet, in_reply_to_status_id=a["id"], auto_populate_reply_metadata=True)
        time.sleep(waitTime * 60)


postTweets()


