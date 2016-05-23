__author__ = 'smurpheus'
import struct
from getpass import getpass
from steam import SteamClient
from steam.enums import EResult
from steam.enums.emsg import EMsg
from listing_manager import Listing, ListingReceiver
from csgo.enums import ECsgoGCMsg
from dbconnector import DBConnector
from threading import Thread, Lock
from steam.core.msg import GCMsgHdr, GCMsgHdrProto
import requests
from csgo import CSGOClient

wildmw = (0, 0.088, 88,
          [r"http://steamcommunity.com/market/listings/730/MAG-7%20%7C%20Praetorian%20(Minimal%20Wear)",
           r"http://steamcommunity.com/market/listings/730/Five-SeveN%20%7C%20Triumvirate%20(Minimal%20Wear)",
           r"http://steamcommunity.com/market/listings/730/MP7%20%7C%20Impire%20(Minimal%20Wear)"])
wildfn = (1, 0.02, 155,
          [r"http://steamcommunity.com/market/listings/730/MAG-7%20%7C%20Praetorian%20(Factory%20New)",
           r"http://steamcommunity.com/market/listings/730/Five-SeveN%20%7C%20Triumvirate%20(Factory%20New)",
           r"http://steamcommunity.com/market/listings/730/MP7%20%7C%20Impire%20(Factory%20New)"])

revolvomw = (1, 0.088, 95,
             [
                 r"http://steamcommunity.com/market/listings/730/StatTrak%E2%84%A2%20SCAR-20%20%7C%20Outbreak%20(Minimal%20Wear)",
                 r"http://steamcommunity.com/market/listings/730/StatTrak%E2%84%A2%20Sawed-Off%20%7C%20Yorick%20(Minimal%20Wear)",
                 r"http://steamcommuity.com/market/listings/730/StatTrak%E2%84%A2%20P2000%20%7C%20Imperial%20(Minimal%20Wear)"])
revolvofn = (1, 0.02, 155,
             [
                 r"http://steamcommunity.com/market/listings/730/StatTrak%E2%84%A2%20P2000%20%7C%20Imperial%20(Factory%20New)",
                 r"http://steamcommunity.com/market/listings/730/StatTrak%E2%84%A2%20SCAR-20%20%7C%20Outbreak%20(Factory%20New)"])
links_plus = [(5, 0.10, 40,
               [
                   r"http://steamcommunity.com/market/listings/730/Dual%20Berettas%20%7C%20Urban%20Shock%20(Minimal%20Wear)",
                   r"http://steamcommunity.com/market/listings/730/Sawed-Off%20%7C%20Serenity%20(Minimal%20Wear)",
                   r"http://steamcommunity.com/market/listings/730/MAC-10%20%7C%20Malachite%20(Minimal%20Wear)"]),
              revolvofn]


links = [r"http://steamcommunity.com/market/listings/730/Dual%20Berettas%20%7C%20Urban%20Shock%20(Minimal%20Wear)",
 r"http://steamcommunity.com/market/listings/730/Sawed-Off%20%7C%20Serenity%20(Minimal%20Wear)",
 r"http://steamcommunity.com/market/listings/730/MAC-10%20%7C%20Malachite%20(Minimal%20Wear)"]

class ItemWatcher(Thread):
    float_lock = Lock()
    def __init__(self, manager, maxnum, maxfloat, maxprice, url):
        Thread.__init__(self)
        self.manager = manager
        self.maxPrice = maxprice
        self.maxNum = maxnum
        self.numToBuy = maxnum
        self.maxFloat = maxfloat,
        self.url = url

    def run(self):
        while self.numToBuy > 0:
            self.manager.request_lock.aquire()
            print "fetching %s"%link
            filtered = self.manager.receive_filtered_listings(self.url, self.maxPrice, self.maxFloat)

            filtered = m.receive_filtered_listings(link, price, wear, slowmode=True)
            for each in filtered:
                print each
                bought = m.buy_item(each)
                if bought:
                    self.numToBuy -= 1
            time.sleep(20)
            time.sleep(60)

class Manager(Thread):
    request_lock = Lock()

    def __init__(self):
        self.logOnDetails = {
                'username': raw_input("Steam user: "),
                'password': getpass("Password: "),
            }
        self.session = None
        self.ready = False
        client = SteamClient()
        self.client = client
        print "Created Client"
        self.client.on('error', self._handle_client_error)
        self.client.on('auth_code_required', self._handle_auth_req)
        self.client.on('logged_on', self._client_handle_logon)
        self.client.on('connected', self._handle_client_connected)
        self.client.on('disconnected', self._handle_client_disconnected)
        self.client.on('reconnected', self._handle_client_reconnected)
        self.client.login(**self.logOnDetails)
        msg, = self.client.wait_event(EMsg.ClientAccountInfo)
        # print "Logged on as: %s" % msg.body.persona_name
        # self.client.run_forever()

    def calc_avg(self, des, max=1, min=0):
        return (des-min)/(max-min)

    def calc_exp_win(self, invest, sells):
        total_sell = 0
        for sell in sells:
            total_sell += (sell*0.85 - invest)
        return float(total_sell)/float(len(sells))

    def _handle_client_reconnected(self, arg=None):
        print "Mofo ist reconnected %s"%arg

    def _handle_client_disconnected(self, arg=None):
        print "Mofo ist disconnected %s"%arg

    def _handle_client_connected(self):
        print "Mofo ist connected"
    def _handle_client_error(self, result):
        print "Error:", EResult(result)

    def _handle_auth_req(self, is_2fa, code_mismatch):
        print "There is an authentication requiered."
        if is_2fa:
            code = raw_input("Enter 2FA Code: ")
            self.logOnDetails.update({'two_factor_code': code})
        else:
            code = raw_input("Enter Email Code: ")
            self.logOnDetails.update({'auth_code': code})

        self.client.login(**self.logOnDetails)

    def _client_handle_logon(self):
        print "Client logon was called!"
        self._connect_go()
        self.client.run_forever()

    def _connect_go(self):
        self.goclient = CSGOClient(self.client)
        self.goclient.on(None, self._handle_gc_message())
        self.goclient.launch()
        self.goclient.on('ready', self._handle_gc_ready())
        # self.client.run_forever()

    def _handle_gc_ready(self):
        print "GC FUCKING RDY"
        self.ready = True

    def _handle_gc_message(self, emsg=None, header=None, payload=None):
        print "gc got something%s  %s  %s"%(emsg,header, payload)

    def get_item_information(self, params):
        self.goclient.send(ECsgoGCMsg.EMsgGCCStrike15_v2_Client2GCEconPreviewDataBlockRequest, params)
        answer, = self.goclient.wait_event(ECsgoGCMsg.EMsgGCCStrike15_v2_Client2GCEconPreviewDataBlockResponse, 10, True)
        return answer.iteminfo

    def get_float_value(self, iteminfo):
        return struct.unpack('f', struct.pack('I', iteminfo.paintwear))[0]

    def buy_item(self, listing):
        if not self.session:
            self.session = self.client.get_web_session()
        session_id = self.session.cookies['sessionid']
        buy_url = 'https://steamcommunity.com/market/buylisting/' + str(listing.id)
        payload = {'quantity': 1, 'sessionid': session_id, 'currency': 3, 'subtotal': listing.price, 'fee': listing.fee,
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

    def receive_all_listings(self, item_link):
        l_receiver = ListingReceiver(item_link)
        if self.goclient.ready:
            listings = l_receiver.get_all_listings()
            for listing in listings:
                saved_listing = db.get_listing_by_id(listing.id)
                if not saved_listing:
                    iteminfo = m.get_item_information(listing.return_param_dict())
                    floatv = m.get_float_value(iteminfo)
                    listing.paintwear = floatv
                    listing.quality = iteminfo.quality
                    listing.paintindex = iteminfo.paintindex
                    print "Float of this item %s index %s" %(floatv, iteminfo.paintindex)
                    time.sleep(1)
                    db.create_listing(listing)
            return listings
        else:
            print "CSGO not ready"
            print "Client %s  logged in %s"%(str(self.client), self.client.logged_on)
            self._connect_go()
            return False

    def receive_filtered_listings(self, item_link, price, wear, slowmode = False):
        filtered = []
        l_receiver = ListingReceiver(item_link, sleep_mode=slowmode)
        if self.goclient.ready:
            listings = l_receiver.get_all_listings()
            print "found %s entries for item" %len(listings)
            inprice = [x for x in listings if x.total_price <= float(price)]
            print "%s with correct price" % len(inprice)
            for listing in listings:
                saved_listing = db.get_listing_by_id(listing.id)
                if listing.total_price <= float(price):
                    if not saved_listing:
                        iteminfo = self.get_item_information(listing.return_param_dict())
                        floatv = self.get_float_value(iteminfo)
                        listing.paintwear = floatv
                        listing.quality = iteminfo.quality
                        listing.paintindex = iteminfo.paintindex
                        db.create_listing(listing)
                        time.sleep(1)
                    if listing.paintwear <= float(wear):
                        # print "Float of this item %s index %s" %(floatv, iteminfo.paintindex)
                        # print "Price: %s; listing id: %s" %(listing.total_price, listing.id)
                        filtered.append(listing)
            print "%s of them with correct wear"%len(filtered)
            return filtered
        else:
            print "CSGO not ready"
            print "Client %s  logged in %s"%(str(self.client), self.client.logged_on)
            self._connect_go()
        return filtered

import time
if __name__ == "__main__":
    m = Manager()
    db = DBConnector()
    print "Items zum Updaten:"
    i = 0
    while not m.ready:
        time.sleep(1)
        print "not yet rdy"
    running = True
    while running:
        item_link = raw_input("What ya wanna do: ")
        if item_link == "exit":
            running = False

        if item_link == "buy":
            item_id = raw_input("Listing ID: ")
            listing = db.get_listing_by_id(item_id)
            if listing:
                db.delete_listing_by_id(listing.id)
                m.buy_item(listing)
            else:
                print "Couldn't find entry for this"
        if item_link == "reconnect":
            m._connect_go()

        if item_link == "item cheaper":
            item_link = raw_input("Link zum Item: ")
            price = raw_input("Billiger als: ")
            wear = raw_input("Besser als: ")
            if "break" not in [item_link, price, wear]:
                filtered = m.receive_filtered_listings(item_link, price, wear)
                if filtered is not None:
                    for each in filtered:
                        print str(each)
                else:
                    time.sleep(4)
                    filtered = m.receive_filtered_listings(item_link, price, wear)
                    if filtered is not None:
                        for each in filtered:
                            print str(each)
                    else:
                        print "Iwas war nich so cool"

        if item_link == "watch links":
            price = 39
            wear = 0.10
            try:
                while True:
                    for link in links:
                        print "fetching %s"%link
                        filtered = m.receive_filtered_listings(link, price, wear, slowmode=True)
                        for each in filtered:
                            print each
                        time.sleep(20)
                    time.sleep(60)
            except KeyboardInterrupt:
                pass

        def fetch_and_buy(num, wear, price, link):
            print "fetching %s" % link
            numbought = 0
            if numbought < num:
                filtered = m.receive_filtered_listings(link, price, wear, slowmode=True)
                for each in filtered:
                    print each
                    bought = None
                    if num > numbought:
                        bought = m.buy_item(each)
                    else:
                        print "Dont need to buy any more."
                    if bought:
                        numbought += 1
                        print "Bought 1 - Need to buy %s more" % (num - numbought)
                    else:
                        print "Couldn't be bought still %s to buy" % (num - numbought)
            return numbought


        if item_link == "watch and buy":
            price = 39
            wear = 0.105
            all_links = links_plus
            nums = [x for x, _, _, _ in all_links]
            total = sum(nums)
            try:
                while total > 0:
                    for item in all_links:
                        num, wear, price, link = item
                        indexofitem = all_links.index(item)
                        if isinstance(link, list):
                            for url in link:
                                bought = fetch_and_buy(num, wear, price, url)
                                num = num - bought
                                all_links[indexofitem] = (num - bought, wear, price, link)
                        else:
                            bought = fetch_and_buy(num, wear, price, link)
                            all_links[all_links.index(item)] = (num - bought, wear, price, link)
                        time.sleep(20)
                    time.sleep(60)
                    nums = [x for x, _, _, _ in all_links]
                    total = sum(nums)
            except KeyboardInterrupt:
                pass
        if item_link == "start observer":
            item = raw_input("Link to the Item: ")
            price = raw_input("Max Price: ")
            wear = raw_input("Max Float: ")
            number = raw_input("How Many Shall be bought: ")
            thread = ItemWatcher(m, number, wear, price, item)







        if item_link == "item":
            item_link = raw_input("Link zum Item: ")
            if not item_link == "break":
                m.receive_all_listings(item_link)


    # rmsg = m.gc.send(msghdr, msg.SerializeToString())
    # print "wooo msg %s" % rmsg
