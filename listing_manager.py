import requests, json
import time
import random
#item_link = raw_input("Gib mir link!:")
    #print r.json()
class Listing(object):
    def __init__(self, name="", paintindex=None, paintwear=None, quality=None, id=None,
                 asset_id=None,d_param=None,total_price=None,price=None, fee=None, url=None, listing_dict=None, asset=None):
        if listing_dict is not None and asset is not None:
            self.create_listing_from_dict(listing_dict, asset, url)
        else:
            self.name = name
            self.paintindex = paintindex
            self.paintwear = paintwear
            self.quality = quality
            self.id = id
            self.asset_id = asset_id
            self.d_parameter = d_param
            self.total_price = total_price
            self.price = price
            self.fee = fee
            self.url = url


    def create_listing_from_dict(self, listing_dict, asset, url):
        if listing_dict["asset"]["id"] in asset.keys():
            self.name = asset[listing_dict["asset"]["id"]]["name"]
        else:
            self.name = ""
        self.paintindex = ""
        self.paintwear = ""
        self.quality = ""
        self.url = url
        self.id = listing_dict["listingid"]
        self.asset_id = listing_dict["asset"]["id"]
        self.d_parameter = listing_dict["asset"]["market_actions"][0]['link'].split("%assetid%")[-1][1:]
        if "converted_price" in listing_dict.keys() and "converted_fee" in listing_dict.keys():
            self.total_price = float(listing_dict["converted_price"]) + float(listing_dict["converted_fee"])
            self.price = float(listing_dict["converted_price"])
            self.fee = float(listing_dict["converted_fee"])
        else:
            self.total_price = float(listing_dict["price"]) + float(listing_dict["fee"])
            self.price = float(listing_dict["price"])
            self.fee = float(listing_dict["fee"])

    def return_param_dict(self):
        params = {
            "param_s": 0,
            "param_a": int(self.asset_id),
            "param_d": int(self.d_parameter),
            "param_m": int(self.id)
        }
        return params

    def create_rungame_serialization(self):
        return "M%sA%s%s"%(self.id,self.asset_id,self.d_parameter)
    def __str__(self):
        return "%s(%r)" % (self.__class__, self.__dict__)
        
class ListingReceiver(object):
    overview_base_url = "http://steamcommunity.com/market/priceoverview/?country=DE&currency=3&appid=730&market_hash_name="
    market_listing_base_url = "http://steamcommunity.com/market/listings/730/"
    listing_manipulator = "/render?start=%s&count=%s&currency=3&language=german&format=json"
    
    def __init__(self, item_url, sleep_mode = False):
        self.sleep_mode = sleep_mode
        self.extracted_item = item_url.split("/")[-1]
        self.item_url = item_url
        priceoverview_url = item_url + self.listing_manipulator%(0,1)
        self.user_agent = {'User-agent': 'Mozilla/5.0'}
        def requesting(url, header):
            timeouttime = random.randrange(40, 90)
            r = requests.get(priceoverview_url, headers=header)
            if r.ok:
                return r
            elif r.status_code == 429:
                print "woooops steam is pissed i'm waiting for %s seconds"%timeouttime
                time.sleep(timeouttime)
                return requesting(url, header)
            else:
                print "Request Failed %s with url %s" % (r, url)
                return False
        r = requesting(item_url, self.user_agent)
        if r and r.ok:
            self.volume = int(r.json()["total_count"])
            self.pages = range(0, self.volume, 100)
            if self.volume/100 > 15:
                self.pages = range(0, 1500, 100)
        else:
            print "Request Failed %s with url %s" % (r, priceoverview_url)
        
    def get_items(self, start, count=100):
        timeouttime = random.randrange(40, 90)
        listing_url = self.item_url + self.listing_manipulator % (start, count)
        if self.sleep_mode:
            time.sleep(random.randrange(1, 10))
        def requesting(url, header):
            r = requests.get(url, headers=header)
            if r.ok:
                data = r.json()
                return data['listinginfo'], data['assets']['730']['2']
            elif r.status_code == 429:
                print "woooops steam is pissed i'm waiting for %s seconds"%timeouttime
                time.sleep(timeouttime)
                return requesting(url, header)
            else:
                print "Request Failed %s with url %s" % (r, url)
                return False, False
        return requesting(listing_url, self.user_agent)
        
    def get_all_items(self):
        datas = {}
        assets = {}
        for start in self.pages:
            count = 100
            if self.pages.index(start) == len(self.pages) - 1:
                count = self.volume % 100
            data, assets = self.get_items(start, count)
            if data and assets:
                datas.update(data)
                assets.update(assets)
            else:
                import sys
                sys.exit()
        return datas, assets

    def get_all_listings(self):
        datas, assets = self.get_all_items()
        return self.evaluate_listing(datas, assets)

    def evaluate_listing(self, listings, assets=None):
        self.listings = [Listing(url=self.item_url, listing_dict=value, asset=assets) for key, value in listings.iteritems()]
        # for key, value in listings.iteritems():
        #     print str(Listing(value))
        return self.listings

                
           
#lr = ListingReceiver(item_link)
#datas = lr.get_all_items()
#lr.evaluate_listing(datas)
