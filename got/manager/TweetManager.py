import urllib,urllib2,json,re,datetime,sys,cookielib
from .. import models
from pyquery import PyQuery
import requests
import time

class TweetManager:

	def __init__(self):
		pass

	@staticmethod
	def getTweets(tweetCriteria, receiveBuffer = None, bufferLength = 100, onDidReceiveTweet = None):
		refreshCursor = ''

		results = []
		resultsAux = []
		cookieJar = cookielib.CookieJar()

		active = True

		while active:
			json = TweetManager.getJsonReponse(tweetCriteria, refreshCursor, cookieJar)
			if len(json['items_html'].strip()) == 0:
				break

			refreshCursor = json['min_position']
			tweets = PyQuery(json['items_html'])('div.js-stream-tweet')

			if len(tweets) == 0:
				break

			for tweetHTML in tweets:
				tweetPQ = PyQuery(tweetHTML)
				tweet = models.Tweet()

				usernameTweet = tweetPQ("span.username.js-action-profile-name b").text();
				txt = re.sub(r"\s+", " ", tweetPQ("p.js-tweet-text").text().replace('# ', '#').replace('@ ', '@'));
				retweets = int(tweetPQ("span.ProfileTweet-action--retweet span.ProfileTweet-actionCount").attr("data-tweet-stat-count").replace(",", ""));
				favorites = int(tweetPQ("span.ProfileTweet-action--favorite span.ProfileTweet-actionCount").attr("data-tweet-stat-count").replace(",", ""));
				dateSec = int(tweetPQ("small.time span.js-short-timestamp").attr("data-time"));
				id = tweetPQ.attr("data-tweet-id");
				permalink = tweetPQ.attr("data-permalink-path");

				geo = ''
				geoSpan = tweetPQ('span.Tweet-geo')
				if len(geoSpan) > 0:
					geo = geoSpan.attr('title')

				tweet.id = id
				tweet.permalink = 'https://twitter.com' + permalink
				tweet.username = usernameTweet
				tweet.text = txt
				tweet.date = datetime.datetime.fromtimestamp(dateSec)
				tweet.retweets = retweets
				tweet.favorites = favorites
				tweet.mentions = " ".join(re.compile('(@\\w*)').findall(tweet.text))
				tweet.hashtags = " ".join(re.compile('(#\\w*)').findall(tweet.text))
				tweet.geo = geo
				if onDidReceiveTweets:
					onDidReceiveTweets(tweet)
				results.append(tweet)
				resultsAux.append(tweet)

				if receiveBuffer and len(resultsAux) >= bufferLength:
					receiveBuffer(resultsAux)
					resultsAux = []

				if tweetCriteria.maxTweets > 0 and len(results) >= tweetCriteria.maxTweets:
					active = False
					break


		if receiveBuffer and len(resultsAux) > 0:
			receiveBuffer(resultsAux)

		return results

	@staticmethod
	def getJsonReponse(tweetCriteria, refreshCursor, cookieJar):
		url = "https://twitter.com/i/search/timeline?f=tweets&q=%s&src=typd&max_position=%s"

		urlGetData = ''
		if hasattr(tweetCriteria, 'username'):
			urlGetData += ' from:' + tweetCriteria.username

		if hasattr(tweetCriteria, 'since'):
			urlGetData += ' since:' + tweetCriteria.since

		if hasattr(tweetCriteria, 'until'):
			urlGetData += ' until:' + tweetCriteria.until

		if hasattr(tweetCriteria, 'querySearch'):
			urlGetData += ' ' + tweetCriteria.querySearch

		if hasattr(tweetCriteria, 'allTweets'):
			if tweetCriteria.allTweets:
				url = "https://twitter.com/i/search/timeline?f=tweets&q=%s&src=typd&max_position=%s"

		url = url % (urllib.quote(urlGetData), refreshCursor)
		user_agent = "Mozilla/5.0 (Windows NT 6.1; Win64; x64)"
		headers = {
			'Host': "twitter.com",
			'User-Agent': user_agent,
			'Accept': "application/json, text/javascript, */*; q=0.01",
			'Accept-Language': "de,en-US;q=0.7,en;q=0.3",
			'X-Requested-With': "XMLHttpRequest",
			'Referer': url,
			'Connection': "keep-alive",
		}
		proxies = {
		  'http': 'socks5://202.69.71.210:1080',
		}
		response = download_with_retries(url, cookies=cookieJar, headers=headers, timeout=180)
		jsonResponse = response.text
		dataJson = json.loads(jsonResponse)
		return dataJson

def download_with_retries(url, cookies, headers, timeout, retries_left=3):
	if (retries_left == 0):
		raise Exception('out of retries for individual url.')
	try:
		return requests.get(url, cookies=cookies, headers=headers)
	except Exception as e:
		print 'failed for individual url, retrying in 5 seconds.'
		time.sleep(5)
		return download_with_retries(url, cookies, headers, timeout, retries_left-1)
