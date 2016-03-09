import requests, json


item_link = raw_input("Gib mir link!:")





    #print r.json()
class Listing(object):
    def __init__(self, listing_dict):
        print listing_dict
        self.id = listing_dict["listingid"]
        self.asset_id = listing_dict["asset"]["id"]
        self.d_parameter = listing_dict["asset"]["market_actions"][0]['link'].split("%assetid%")[-1]
        if "converted_price" in listing_dict.keys() and "converted_fee" in listing_dict.keys():
            self.total_price = float(listing_dict["converted_price"]) + float(listing_dict["converted_fee"])
            self.price = float(listing_dict["converted_price"])
            self.fee = float(listing_dict["converted_fee"])
        else:
            self.total_price = float(listing_dict["price"]) + float(listing_dict["fee"])
            self.price = float(listing_dict["price"])
            self.fee = float(listing_dict["fee"])
    def __str__(self):
        return "%s(%r)" % (self.__class__, self.__dict__)
        
class ListingReceiver(object):
    overview_base_url = "http://steamcommunity.com/market/priceoverview/?country=DE&currency=3&appid=730&market_hash_name="
    market_listing_base_url = "http://steamcommunity.com/market/listings/730/"
    listing_manipulator = "/render?start=%s&count=%s&currency=3&language=german&format=json"
    
    def __init__(self, item_url):
        self.extracted_item = item_url.split("/")[-1]
        self.item_url = item_url
        priceoverview_url = item_url + self.listing_manipulator%(0,1)
        r = requests.get(priceoverview_url)
        if r.ok:
            self.volume = int(r.json()["total_count"])
            self.pages = range(0,self.volume,100)
            if self.volume/100 > 10:
                self.pages= range(0,1000,100)
        else:
            print "Request Failed %s with url %s" % (r, priceoverview_url)
        
    def get_items(self, start, count = 100):
        listing_url = self.item_url + self.listing_manipulator%(start, count)
        r = requests.get(listing_url)
        if r.ok:
            data = r.json()
            return data['listinginfo']
        else:
            print "Request Failed %s with url %s" % (r, listing_url)
        
    def get_all_items(self):
        datas = {}
        for start in self.pages:
            count = 100
            if self.pages.index(start) == len(self.pages) - 1:
                count = self.volume % 100
            data = self.get_items(start, count)
            datas.update(data)
        return datas
            
    def evaluate_listing(self, listings):
        for key, value in listings.iteritems():
            print str(Listing(value))

                
           
lr = ListingReceiver(item_link)
datas = lr.get_all_items()
lr.evaluate_listing(datas)
