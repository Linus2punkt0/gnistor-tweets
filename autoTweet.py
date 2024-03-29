# -*- coding: utf-8 -*-
from twython import Twython
from datetime import datetime, timedelta
import time, os, feedparser, pytz
import auth
import paths
import locale

tz = pytz.timezone("Europe/Stockholm")
curTime = datetime.now(tz)
timeLimit = curTime - timedelta(hours = 1)
basePath = paths.basePath
logPath = paths.logPath
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
    eventTime = datetime.strptime(post.gnistor_startdate, '%a, %d %b %Y %X %z')
    if len(post.gnistor_organizer) > 0 and post.gnistor_organizer not in post.title:
        eventTitle = post.gnistor_organizer + " anordnar " + post.title
    else:
        eventTitle = post.title
    if (eventTime > curTime):
        item = {
            "title": eventTitle,
            "shortTitle": post.title,
            "eventTime": eventTime,
            "url": post.link,
            "location": post.gnistor_locations
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
        writeLog("Following podcast episodes found: \n" + "\n".join(tweets))
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

def getEventInfo(title, eventTime, location, url):
		if (eventTime.strftime("%Y") != curTime.strftime("%Y")):
			timestamp = eventTime.strftime("%-d/%-m %Y %H:%M")
		else:
			timestamp = eventTime.strftime("%-d/%-m %H:%M")
		if (len(location) > 0):
			eventInfo = title + "\nNär: " + timestamp + "\nVar: " + location + "\n" + url
		else:
			eventInfo = title + "\nNär: " + timestamp + "\n" + url
		return eventInfo


def getNewEvents():
    if (os.path.exists(localCal)):
        localEvents = []
        with open(localCal, 'r') as cal:
            for line in cal:
                eventArr = line.replace('\n', "").split(',')
                url = eventArr[0]
                eventTime = datetime.strptime(eventArr[1], '%Y-%m-%d  %X%z')
                if (eventTime > curTime):
                    localEvents.append(url)
        if (len(localEvents) > 0):
            tweets = []
            for post in posts:
                eventTime = post["eventTime"]
                url = post["url"]
                location = post["location"]
                if (eventTime > curTime and url not in localEvents):
                    title = post["title"]
                    writeLog("New event: " + title)
                    eventInfo = getEventInfo(title, eventTime, location, url)
                    writeLog("Eventinfo: " + eventInfo)
                    if (len(tweets) == 0):
                        tweets.append("Nya evenemang har lagts till i kalendern:")
                    tweets.append(eventInfo)
            if (len(tweets) > 1):
                queue.append(tweets)
                writeLog("Following new events found: \n" + "\n".join(tweets))
            else:
                writeLog("No new events in the calendar")

def comingWeek():
    tweets = []
    for post in posts:
        eventTime = post["eventTime"]
        url = post["url"]
        if (eventTime.isocalendar()[1] == curTime.isocalendar()[1] + 1):
            location = post["location"]
            title = post["title"]
            eventInfo = getEventInfo(title, eventTime, location, url)
            if (len(tweets) == 0):
                tweets.append("Här är händelserna för den kommande veckan:")
            tweets.append(eventInfo)
    if (len(tweets) > 1):
        queue.append(tweets)
        writeLog("Following events found for the coming week: \n" + "\n".join(tweets))
    else:
        writeLog("No events in the coming week")

def comingMonth():
    saved = locale._setlocale(locale.LC_TIME)
    locale.setlocale(locale.LC_TIME, 'sv_SE')
    month = (curTime+timedelta(days=1)).strftime('%B')
    locale.setlocale(locale.LC_TIME, saved)
    tweets = []
    for post in posts:
        eventTime = post["eventTime"]
        url = post["url"]
        if ((curTime+timedelta(days=1)).month == curTime.month and eventTime.year == (curTime+timedelta(days=1)).year):
            title = post["title"]
            location = post["location"]
            eventInfo = getEventInfo(title, eventTime, location, url)
            if (len(tweets) == 0):
                tweets.append("Här är alla händelser i kalendern för " + month + ":")
            tweets.append(eventInfo)
    if (len(tweets) > 1):
        queue.append(tweets)
        writeLog("Following events found for the coming month: \n" + "\n".join(tweets))
    else:
        writeLog("No events in the coming month")

def todayTomorrow():
    todays = []
    tomorrows = []
    for post in posts:
        eventTime = post["eventTime"]
        url = post["url"]
        title = post["title"]
        location = post["location"]
        eventInfo = getEventInfo(title, eventTime, location, url)
        if (eventTime.date() == curTime.date()):
            if (len(todays) == 0):
                todays.append("Här är dagens evenemang:")
            todays.append(eventInfo)
        elif (eventTime.date() == curTime.date() + timedelta(days=1)):
            if (len(tomorrows) == 0):
                tomorrows.append("Här är vad som händer imorgon:")
            tomorrows.append(eventInfo)
    if (len(todays) > 1):
        queue.append(todays)
        writeLog("Following events found for today: \n" + "\n".join(todays))
    else:
        writeLog("No events for today")
    if (len(tomorrows) > 1):
        queue.append(tomorrows)
        writeLog("Following events found for tomorrow: \n" + "\n".join(tomorrows))
    else:
        writeLog("No events for tomorrow")

def inTwoHours():
    tweets = []
    tweeted = False;
    for post in posts:
        eventTime = post["eventTime"]
        url = post["url"]
        if (curTime+timedelta(hours=1) < eventTime < curTime+timedelta(hours=2)):
            tweeted = True
            location = post["location"]
            title = post["shortTitle"]
            if (len(location) > 0):
                if (location == "Internet"):
                    location = " på " + location
                else:
                    location = " i " + location
                queue.append("Nu börjar snart " + title + location + "! \n" + url)
            else:
                queue.append("Nu börjar snart " + title + "! \n" + url)
            writeLog("Following evenemang found for the next two hours: \n" + "\n".join(tweets))
    if (not tweeted):
        writeLog("No events coming up in the next two hours")

def gatherPosts():
    inTwoHours()
    if (isLastOfMonth() and curTime.hour == 9):
        comingMonth()
    elif (curTime.weekday() == 6 and curTime.hour == 17):
        comingWeek()
    elif (curTime.hour == 9):
        todayTomorrow()
    getPodTweets()
    getNewEvents()
    saveLocalCalendar()

def isLastOfMonth():
    today = curTime.month
    tomorrow = (curTime+timedelta(days=1)).month
    if (today != tomorrow):
        return True
    else:
        return False

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
    for section in queue:
        a = ""
        if (isinstance(section, str)):
            writeLog("Following tweet found in current section: " + section)
            a = twitter.update_status(status=section, auto_populate_reply_metadata=True)
        else:
            writeLog("Following tweets found in current section: " + ", ".join(section))
            for tweet in section:
                if (len(a) == 0):
                    writeLog("Posting tweet: " + tweet)
                    a = twitter.update_status(status=tweet, auto_populate_reply_metadata=True)
                else:
                    writeLog("Posting tweet: " + tweet + " as a reply")
                    a = twitter.update_status(status=tweet, in_reply_to_status_id=a["id"], auto_populate_reply_metadata=True)
            writeLog("Reply from Twitter: " + str(a))
        time.sleep(waitTime * 60)


postTweets()


