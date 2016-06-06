from listing_manager import ListingReceiver
from manager import MyClient
from dbconnector import DBConnector
from WebCommunicator import TimeoutCalculator, Communicator
import time
from eventemitter import EventEmitter
from Queue import Queue
import thread
from csgo.msg import get_emsg_enum, find_proto
from threading import Thread, Timer, RLock, Event

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
            self.goclient = MyClient(False)
            self.goclient.on("READY", self.clientrdy)
        self.db = None
        self.db_lock = RLock()

    def clientrdy(self):
        print("goclient is ready!")
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
        l_receiver = ListingReceiver(item_link, self.timeouter, self.goclient.client.get_web_session())
        if self.goclient.goclient.ready:
            listings = l_receiver.get_all_listings(maxnum)
            print("found %s entries for item" % len(listings))
            inprice = [x for x in listings if x.total_price <= float(price)]
            print("%s with correct price" % len(inprice))
            for listing in listings:
                with self.db_lock:
                    db = DBConnector()
                    saved_listing = db.get_listing_by_id(listing.id)
                    if listing.total_price <= float(price):
                        if not saved_listing:
                            iteminfo = self.goclient.get_item_information(listing.return_param_dict())
                            time.sleep(0.2)
                            if iteminfo:
                                floatv = self.goclient.get_float_value(iteminfo)
                                listing.paintwear = floatv
                                listing.quality = iteminfo.quality
                                listing.paintindex = iteminfo.paintindex
                                db.create_listing(listing)
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
            db = DBConnector()
            with self.db_lock:
                lines = file.readlines()
                for line in lines[1:]:
                    item, number, maxfloat, maxprice, buygrp, dealno, dealname = line.split(";")
                    item = item.replace(" ", "")
                    print("%s %s,%s,%s,%s" % (lines.index(line), item.replace(" ",""), number, maxfloat, maxprice))
                    deal = db.get_deal_by_name(dealname)
                    if not deal:
                        db.create_deal(dealname)
                        deal = db.get_deal_by_name(dealname)
                    
                    indb = db.get_buy_order(item, maxfloat)
                    if not indb:
                        db.create_buy_order(item, number,maxfloat,maxprice)
                    else:
                        print(indb)

    def work_info_q(self):
        while not self.listingq.empty():
            listing = self.listingq.get(True, 10)
            # print("Input Listing %s"%listing)
            with self.db_lock:
                db = DBConnector()
                saved_listing = db.get_listing_by_id(listing.id)
                # print("Listing in work %s"%listing)
                if not saved_listing:
                    # print(listing.return_param_dict())
                    iteminfo = self.goclient.get_item_information(listing.return_param_dict())
                    # time.sleep(0.2)
                    if iteminfo:
                        floatv = self.goclient.get_float_value(iteminfo)
                        print("Float value aquired %s" % floatv)
                        listing.paintwear = floatv
                        listing.quality = iteminfo.quality
                        listing.paintindex = iteminfo.paintindex
                        db.create_listing(listing)
                        self.listingqfull.put(listing, True, 10)
                else:
                    pass
                    # print("List

    def printOutput(self):
        while 1==1:
            if not self.listingq.empty():
                print self.listingq.get(True, 10)


    def fetch_listings_for_deals(self):
        with self.db_lock:
            db = DBConnector()
            orders = db.get_all_buy_orders()
            for item, number, maxfloat, maxprice in orders:
                print self.receive_filtered_listings(item, maxprice, maxfloat, maxnum=100)

    def fill_queue(self):
        with self.db_lock:
            print("Filling Queue!!!!!")
            db = DBConnector()
            orders = db.get_all_buy_orders()
            for item, number, maxfloat, maxprice in orders:
                self.urlq.put(item, timeout=10)

class ListingFetcher(Thread):

    def __init__(self, inputqueue, output, timeouter, db):
        thread = Thread(target=self.run, args=())
        thread.daemon = True  # Daemonize thread
        self.running = False
        self.input = inputqueue
        self.output = output
        self.timeouter = timeouter
        thread.start()


    def run(self):
        self.running = True
        while self.running:
            if not self.input.empty():
                url = self.input.get(True, 10)
                # print("Querying url")
                receiver = ListingReceiver(url, self.timeouter)
                listings = receiver.get_all_listings(100)
                for listing in listings:
                    self.output.put(listing, True, 10)
            else:
                # print("Deal Queue Empty!")
                time.sleep(5)


class FillQueue(Thread):
    def __init__(self, event, client):
        thread = Thread(target=self.run, args=())
        thread.daemon = True  # Daemonize thread
        self.stopped = event
        self.client = client
        thread.start()

    def run(self):
        while not self.stopped.wait(60):
            self.client.fill_queue()

class Buyer(Thread):
    def __init__(self, event, client):
        thread = Thread(target=self.run, args=())
        thread.daemon = True  # Daemonize thread
        self.stopped = event
        self.client = client
        self.web = Communicator(self.client.timeouter, self.client.goclient.client.get_web_session())
        thread.start()

    def run(self):
        while not self.stopped.wait(10):
            with self.client.db_lock:
                db = DBConnector()
                buyorders = db.get_all_buy_orders()
                print "Buyorders fetched"
                for item, number, maxfloat, maxprice in buyorders:
                    if number >= 1:
                        listings = db.get_listing_for_url(item)
                        fitting = [x for x in listings if x.total_price <= float(maxprice) and x.paintwear <= float(maxfloat)]
                        for item in fitting:
                            print("BUYING ITEM!!!!!!!!!!!!!!!")
                            saved = db.save_bought_item(item, maxfloat)
                            if not saved:
                                print ("COULD NOT BE SAVED!!!")


if __name__ == "__main__":
    f = FloatFetcher()
    f.goclient.wait_event("READY")
    f.get_deals()

    f.fill_queue()
    # f.fetch_listings_for_deals()
    lf = ListingFetcher(f.urlq, f.listingq, f.timeouter, f.db)
    buyer = Buyer(Event(), f)
    # qfiller = FillQueue(Event(), f)
    try:
        while True:
            f.work_info_q()
            time.sleep(10)
    except KeyboardInterrupt:
        pass
    # t = thread.start_new_thread(f.printOutput, ())
    raw_input("Waiting")
    buyer.stopped.set()
    # qfiller.stopped.set()
    lf.running = False

    # while not f.listingqfull.empty():
    #     print("Iteminfor %s"%f.listingqfull.get())


    # f.fetch_listings_for_deals()
