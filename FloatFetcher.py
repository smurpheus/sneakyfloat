from listing_manager import ListingReceiver
from manager import MyClient
from dbconnector import DBConnector
class FloatFetcher(object):
    def __init__(self):
        self.conffile = "deals.csv"
        self.goclient = MyClient()
        self.db = DBConnector()
    def calc_avg(self, des, max=1, min=0):
        return (des - min) / (max - min)

    def calc_exp_win(self, invest, sells):
        total_sell = 0
        for sell in sells:
            total_sell += (sell * 0.85 - invest)
        return float(total_sell) / float(len(sells))

    def receive_all_listings(self, item_link):
        return self.receive_filtered_listings(item_link)

    def receive_filtered_listings(self, item_link, price=10**10, wear=10, slowmode=False):
        filtered = []
        l_receiver = ListingReceiver(item_link)
        if self.goclient.goclient.ready:
            listings = l_receiver.get_all_listings()
            print("found %s entries for item" % len(listings))
            inprice = [x for x in listings if x.total_price <= float(price)]
            print("%s with correct price" % len(inprice))
            for listing in listings:
                saved_listing = self.db.get_listing_by_id(listing.id)
                if listing.total_price <= float(price):
                    if not saved_listing:
                        iteminfo = self.get_item_information(listing.return_param_dict())
                        floatv = self.get_float_value(iteminfo)
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
            print("Client %s  logged in %s" % (str(self.client), self.client.logged_on))
            self._connect_go()
        return filtered

    def get_deals(self):
        with open(self.conffile, "r") as file:
            lines = file.readlines()
            for line in lines:
                line.split(";")
if __name__ == "__main__":
    pass