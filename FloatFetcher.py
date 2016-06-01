from listing_manager import ListingReceiver
from manager import MyClient
from dbconnector import DBConnector
from WebCommunicator import TimeoutCalculator
import time
from eventemitter import EventEmitter
from Queue import Queue
import thread
from threading import Thread

def _chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i:i + n]

class FloatFetcher(EventEmitter):
    goclient = None
    conffile = "./deals.csv"

    def __init__(self, do_login=True):
        self.timeouter = TimeoutCalculator()
        self.urlq = Queue()
        self.listingq = Queue()
        self.listingqfull = Queue()
        if do_login:
            self.goclient = MyClient()
            self.goclient.on("READY", self.clientrdy)
        self.db = DBConnector()

    def clientrdy(self):
        self.emit("READY")

    def calc_avg(self, des, max=1, min=0):
        return (des - min) / (max - min)

    def calc_exp_win(self, invest, sells):
        total_sell = 0
        for sell in sells:
            total_sell += (sell * 0.85 - invest)
        return float(total_sell) / float(len(sells))

    def receive_all_listings(self, item_link):
        return self.receive_filtered_listings(item_link)

    def receive_filtered_listings(self, item_link, price=10 ** 10, wear=10, slowmode=False, maxnum=None):
        filtered = []
        l_receiver = ListingReceiver(item_link, self.timeouter)
        if self.goclient.goclient.ready:
            listings = l_receiver.get_all_listings(maxnum)
            print("found %s entries for item" % len(listings))
            inprice = [x for x in listings if x.total_price <= float(price)]
            print("%s with correct price" % len(inprice))
            for listing in listings:
                saved_listing = self.db.get_listing_by_id(listing.id)
                if listing.total_price <= float(price):
                    if not saved_listing:
                        iteminfo = self.goclient.get_item_information(listing.return_param_dict())
                        time.sleep(0.2)
                        if iteminfo:
                            floatv = self.goclient.get_float_value(iteminfo)
                            listing.paintwear = floatv
                            listing.quality = iteminfo.quality
                            listing.paintindex = iteminfo.paintindex
                            self.db.create_listing(listing)
                            if listing.paintwear <= float(wear):
                                # print "Float of this item %s index %s" %(floatv, iteminfo.paintindex)
                                # print "Price: %s; listing id: %s" %(listing.total_price, listing.id)
                                filtered.append(listing)
            print("%s of them with correct wear" % len(filtered))
            return filtered
        else:
            print("CSGO not ready")
            print("Client %s  logged in %s" % (str(self.goclient.client), self.goclient.client.logged_on))
            self.goclient._connect_go()
        return filtered

    def get_deals(self):
        with open(self.conffile, "r") as file:
            lines = file.readlines()
            for line in lines[1:]:
                item, number, maxfloat, maxprice = line.split(";")
                item = item.replace(" ","")
                print("%s %s,%s,%s,%s" % (lines.index(line), item.replace(" ",""), number, maxfloat, maxprice))
                indb = self.db.get_buy_order(item, maxfloat)
                if not indb:
                    self.db.create_buy_order(item, number,maxfloat,maxprice)
                else:
                    print(indb)

    def printOutput(self):
        while 1==1:
            if not self.listingq.empty():
                print self.listingq.get(True, 10)


    def fetch_listings_for_deals(self):
        orders = self.db.get_all_buy_orders()
        for item, number, maxfloat, maxprice in orders:
            print self.receive_filtered_listings(item, maxprice, maxfloat, maxnum=100)

    def fill_queue(self):
        orders = self.db.get_all_buy_orders()
        for item, number, maxfloat, maxprice in orders:
            self.urlq.put(item,timeout=10)

class ListingFetcher(Thread):

    def __init__(self, inputqueue, output, timeouter, db):
        Thread.__init__(self)
        self.running = False
        self.input = inputqueue
        self.output = output
        self.timeouter = timeouter
        self.db = db

    def run(self):
        self.running = True
        while self.running:
            if not self.input.empty():
                url = self.input.get(True, 10)
                receiver = ListingReceiver(url, self.timeouter)
                listings = receiver.get_all_listings(100)
                for listing in listings:
                    self.output.put(listing, True, 10)

class InfoGrabber(Thread):

    def __init__(self, inputqueue, output, goclient, db):
        Thread.__init__(self)
        self.running = False
        self.input = inputqueue
        self.output = output
        self.goclient = goclient
        self.db = db

    def run(self):
        self.running = True
        while self.running:
            if not self.input.empty():
                listing = self.input.get(True, 10)
                iteminfo = self.goclient.get_item_information(listing.return_param_dict())
                time.sleep(0.2)
                if iteminfo:
                    floatv = self.goclient.get_float_value(iteminfo)
                    listing.paintwear = floatv
                    listing.quality = iteminfo.quality
                    listing.paintindex = iteminfo.paintindex
                    self.db.create_listing(listing)
                    self.output.put(listing, True, 10)

if __name__ == "__main__":
    f = FloatFetcher()
    f.get_deals()
    f.wait_event("READY", 10)
    lf = ListingFetcher(f.urlq, f.listingq, f.timeouter, f.db)
    ig = InfoGrabber(f.listingq, f.listingqfull, f.goclient, f.db)
    f.fill_queue()
    lf.start()
    ig.start()
    thread.start_new_thread(f.printOutput, ())
    # f.fetch_listings_for_deals()
