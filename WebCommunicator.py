import requests, json
import time
import math
import requests.exceptions


class TimeoutCalculator(object):
    timeoutLevel = 0
    lasttime = None

    def getTimeout(self):
        lasttimeout = math.exp(self.timeoutLevel)
        curtime = time.time()
        if self.lasttime:
            timedif = curtime - self.lasttime
        else:
            self.lasttime = curtime
        if timedif > lasttimeout:
            self.timeoutLevel -= 1
        else:
            self.timeoutLevel += 1
        timeout = math.exp(self.timeoutLevel)
        self.lasttime = curtime
        return timeout


class Communicator(object):
    def __init__(self, timeouter):
        self.user_agent = {'User-agent': 'Mozilla/5.0'}
        self.timeouter = timeouter

    def requestListingNumber(self, item_url):
        r = self.__doRequest(item_url)
        if r and r.ok:
            return int(r.json()["total_count"])
        else:
            return False

    def requestItems(self, item_url):
        r = self.__doRequest(item_url)
        if r and r.ok:
            return r.json()
        else:
            return False

    def __doRequest(self, url):
        try:
            r = requests.get(url, headers=self.user_agent)
        except requests.exceptions.MissingSchema:
            print "The given URL raised an error %s"%url
            return False
        if r.ok:
            return r
        elif r.status_code == 429:
            timeouttime = self.timeouter.getTimeout()
            print
            "woooops steam is pissed i'm waiting for %s seconds" % timeouttime
            time.sleep(timeouttime)
            return self.__doRequest(url)
        else:
            print
            "Request Failed %s with url %s" % (r, url)
            return False

    def buy_item(self, listing):
        if not self.session:
            self.session = self.client.get_web_session()
        session_id = self.session.cookies['sessionid']
        buy_url = 'https://steamcommunity.com/market/buylisting/' + str(listing.id)
        payload = {'quantity': 1, 'sessionid': session_id, 'currency': 3, 'subtotal': listing.price,
                   'fee': listing.fee,
                   'total': listing.total_price}
        header = {'Host': 'steamcommunity.com',
                  'Connection': 'keep-alive',
                  'Accept': '*/*',
                  'Origin': 'http://steamcommunity.com',
                  'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/31.0.1650.63 Safari/537.36',
                  'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                  'Referer': listing.url,
                  'Accept-Encoding': 'gzip,deflate',
                  'Accept-Language': 'en-US,en;q=0.8,pt;q=0.6,es;q=0.4'
                  }

        buy_request = requests.Request('POST', buy_url, cookies=self.session.cookies, data=payload, headers=header)
        prepared = buy_request.prepare()
        response = self.session.send(prepared)
        if (response.status_code == 200):
            return True
            print("Bought %s for %f\n" % (listing.url, listing.total_price))
        else:
            return False
            print("Couldn't buy %s for %f\n" % (listing.url, listing.total_price))
