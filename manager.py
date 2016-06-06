__author__ = 'smurpheus'
import struct
from getpass import getpass
from steam import SteamClient
from steam.enums import EResult
from steam.enums.emsg import EMsg
from eventemitter import EventEmitter
import gevent
from listing_manager import Listing, ListingReceiver
from csgo.enums import ECsgoGCMsg
from dbconnector import DBConnector
from threading import Thread, Lock
from steam.core.msg import GCMsgHdr, GCMsgHdrProto
import requests
from csgo import CSGOClient
from email_connector import EmailConnector
import time

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
mail = "smurpheus@gmail.com"
user = "smurf3us"

class MyClient(EventEmitter):
    def __init__(self, manual=True):
        self.logOnDetails = {
            'username': raw_input("Steam user: "),
            'password': getpass("Password: "),
        }
        # self.logOnDetails = {
        #     'username': user,
        #     'password': getpass("Password: "),
        # }
        if not manual:
            mail = raw_input("Email Adress: ")
            self.emailer = EmailConnector(mail, getpass("Password: "))
        self.manual = manual
        self.session = None
        self.ready = False
        client = SteamClient()
        self.client = client
        print("Created Client")
        self.client.on('error', self._handle_client_error)
        self.client.on('auth_code_required', self._handle_auth_req)
        self.client.on('logged_on', self._client_handle_logon)
        self.client.on('connected', self._handle_client_connected)
        self.client.on('disconnected', self._handle_client_disconnected)
        self.client.on('reconnected', self._handle_client_reconnected)
        print("Doing login")
        self.client.login(**self.logOnDetails)
        print("Login was sent.")

        # msg, = self.client.wait_event(EMsg.ClientAccountInfo, 20)
        # print "Logged on as: %s" % msg.body.persona_name
        # self.client.run_forever()

    def _handle_client_reconnected(self, arg=None):
        print("Mofo ist reconnected %s" % arg)

    def _handle_client_disconnected(self, arg=None):
        print("Mofo ist disconnected %s" % arg)

    def _handle_client_connected(self):
        print("Mofo ist connected")

    def _handle_client_error(self, result):
        print("Error:", EResult(result))

    def _handle_auth_req(self, is_2fa, code_mismatch):
        print("There is an authentication requiered.")
        if self.manual:
            if is_2fa:
                code = raw_input("Enter 2FA Code: ")
                self.logOnDetails.update({'two_factor_code': code})
            else:
                code = raw_input("Enter Email Code: ")
                self.logOnDetails.update({'auth_code': code})

            self.client.login(**self.logOnDetails)
        else:
            if is_2fa:
                self.emit("mobile_req")
                code = raw_input("Enter 2FA Code: ")
                self.logOnDetails.update({'two_factor_code': code})
            else:
                self.emit("email_req")
                time.sleep(5)
                code = self.emailer.getNewestCode()
                print("LOGIN CODE %s"%code)
                self.logOnDetails.update({'auth_code': code})

            self.client.login(**self.logOnDetails)

    def _client_handle_logon(self):
        print("Client logon was called!")
        self._connect_go()
        self.client.run_forever()

    def _connect_go(self):
        self.goclient = CSGOClient(self.client)
        self.goclient.launch()
        # self.goclient.on(None, self._handle_gc_message)
        self.goclient.on(ECsgoGCMsg.EMsgGCCStrike15_v2_Client2GCEconPreviewDataBlockResponse, self.safe_to_queue)
        self.goclient.on('ready', self._handle_gc_ready)
        # self.client.run_forever()

    def _handle_gc_ready(self):
        print("GC FUCKING RDY")
        self.ready = True
        self.emit("READY")

    def _handle_gc_message(self, emsg = None, msg=None):
        print("handle GC was called")
        print("msg: %s" % (msg))
        print("emsg: %s" % (emsg))

    def get_item_information(self, params):
        # print("get item info called with %s"%params)
        try:
            self.goclient.send(ECsgoGCMsg.EMsgGCCStrike15_v2_Client2GCEconPreviewDataBlockRequest, params)
            answer, = self.goclient.wait_event(ECsgoGCMsg.EMsgGCCStrike15_v2_Client2GCEconPreviewDataBlockResponse, 10,
                                               True)
            # print("Got an answer %s" % answer)
        except gevent.timeout.Timeout:
            print("Timed out for %s"%params)
            return False
        return answer.iteminfo

    def get_item_information_async(self, params):
        # print("get item info called with %s"%params)
        print self.goclient.connection_status
        self.goclient.send(ECsgoGCMsg.EMsgGCCStrike15_v2_Client2GCEconPreviewDataBlockRequest, params)
        print "Send stuff"


    def safe_to_queue(self, emsg=None, msg=None):
        print("Many stuff got%s  %s " % (emsg, msg))
        # print("Got an answer %s" % answer)


    def get_float_value(self, iteminfo):
        return struct.unpack('f', struct.pack('I', iteminfo.paintwear))[0]

# import time
# if __name__ == "__main__":
#     print( "Items zum Updaten:")
#     i = 0
#     while not m.ready:
#         time.sleep(1)
#         print( "not yet rdy")
#     running = True
#     while running:
#         item_link = raw_input("What ya wanna do: ")
#         if item_link == "exit":
#             running = False
#
#         if item_link == "buy":
#             item_id = raw_input("Listing ID: ")
#             listing = db.get_listing_by_id(item_id)
#             if listing:
#                 db.delete_listing_by_id(listing.id)
#                 m.buy_item(listing)
#             else:
#                 print( "Couldn't find entry for this")
#         if item_link == "reconnect":
#             m._connect_go()
#
#         if item_link == "item cheaper":
#             item_link = raw_input("Link zum Item: ")
#             price = raw_input("Billiger als: ")
#             wear = raw_input("Besser als: ")
#             if "break" not in [item_link, price, wear]:
#                 filtered = m.receive_filtered_listings(item_link, price, wear)
#                 if filtered is not None:
#                     for each in filtered:
#                         print( str(each))
#                 else:
#                     time.sleep(4)
#                     filtered = m.receive_filtered_listings(item_link, price, wear)
#                     if filtered is not None:
#                         for each in filtered:
#                             print( str(each))
#                     else:
#                         print( "Iwas war nich so cool")
#
#         if item_link == "watch links":
#             price = 39
#             wear = 0.10
#             try:
#                 while True:
#                     for link in links:
#                         print( "fetching %s"%link)
#                         filtered = m.receive_filtered_listings(link, price, wear, slowmode=True)
#                         for each in filtered:
#                             print( each)
#                         time.sleep(20)
#                     time.sleep(60)
#             except KeyboardInterrupt:
#                 pass
#
#         def fetch_and_buy(num, wear, price, link):
#             print( "fetching %s" % link)
#             numbought = 0
#             if numbought < num:
#                 filtered = m.receive_filtered_listings(link, price, wear, slowmode=True)
#                 for each in filtered:
#                     print( each)
#                     bought = None
#                     if num > numbought:
#                         bought = m.buy_item(each)
#                     else:
#                         print( "Dont need to buy any more.")
#                     if bought:
#                         numbought += 1
#                         print( "Bought 1 - Need to buy %s more" % (num - numbought))
#                     else:
#                         print( "Couldn't be bought still %s to buy" % (num - numbought))
#             return numbought
#
#
#         if item_link == "watch and buy":
#             price = 39
#             wear = 0.105
#             all_links = links_plus
#             nums = [x for x, _, _, _ in all_links]
#             total = sum(nums)
#             try:
#                 while total > 0:
#                     for item in all_links:
#                         num, wear, price, link = item
#                         indexofitem = all_links.index(item)
#                         if isinstance(link, list):
#                             for url in link:
#                                 bought = fetch_and_buy(num, wear, price, url)
#                                 num = num - bought
#                                 all_links[indexofitem] = (num - bought, wear, price, link)
#                         else:
#                             bought = fetch_and_buy(num, wear, price, link)
#                             all_links[all_links.index(item)] = (num - bought, wear, price, link)
#                         time.sleep(20)
#                     time.sleep(60)
#                     nums = [x for x, _, _, _ in all_links]
#                     total = sum(nums)
#             except KeyboardInterrupt:
#                 pass
#         if item_link == "start observer":
#             item = raw_input("Link to the Item: ")
#             price = raw_input("Max Price: ")
#             wear = raw_input("Max Float: ")
#             number = raw_input("How Many Shall be bought: ")
#
#         if item_link == "item":
#             item_link = raw_input("Link zum Item: ")
#             if not item_link == "break":
#                 m.receive_all_listings(item_link)
#
#
#     # rmsg = m.gc.send(msghdr, msg.SerializeToString())
#     # print "wooo msg %s" % rmsg
