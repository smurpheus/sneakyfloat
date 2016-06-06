__author__ = 'smurpheus'
import sqlite3
from listing_manager import Listing


class DBConnector(object):
    def __init__(self):
        self.con = sqlite3.connect('itemstorage.db')

    def create_listing(self, listing):
        statement = "INSERT INTO listings VALUES(%s,%s,%s,'%s',%s,%s,%s,%s,%s, '%s', %s)" % (
        listing.id, listing.asset_id,
        listing.d_parameter, listing.name, listing.price,
        listing.total_price, listing.paintwear, listing.quality,
        listing.paintindex, listing.url, listing.fee)
        cur = self.con.cursor()
        cur.execute(statement)
        self.con.commit()

    def get_listing_by_id(self, listing_id):
        cur = self.con.cursor()
        results = cur.execute("SELECT * from listings WHERE Id=%s" % listing_id).fetchall()
        if len(results) < 1:
            return False
        result = results[0]
        return Listing(id=result[0], asset_id=result[1], d_param=result[2], name=result[3], price=result[4],
                       total_price=result[5], paintwear=result[6], quality=result[7], paintindex=result[8],
                       url=result[9], fee=result[10])

    def delete_listing_by_id(self, listing_id):
        cur = self.con.cursor()
        cur.execute("DELETE from listings WHERE Id=%s" % listing_id)

    def get_listing_for_url(self, url):
        cur = self.con.cursor()
        results = cur.execute("SELECT * from listings WHERE url='%s'" % url).fetchall()
        listings = []
        for result in results:
            listings.append(Listing(id=result[0], asset_id=result[1], d_param=result[2], name=result[3], price=result[4],
                    total_price=result[5], paintwear=result[6], quality=result[7], paintindex=result[8],
                    url=result[9], fee=result[10]))
        return listings

    def create_buy_order(self, item, number, maxfloat, maxprice):
        result = self.get_buy_order(item, maxfloat)
        if result:
            return False
        statement = "INSERT INTO buyorders VALUES ('%s', %s, %s,%s)" % (item, number, maxfloat, maxprice)
        print(statement)
        cur = self.con.cursor()
        cur.execute(statement)
        self.con.commit()

    def get_buy_order(self, item, maxfloat):
        cur = self.con.cursor()
        statement = "SELECT * FROM buyorders where item='%s' and maxfloat=%s" % (item, maxfloat)
        results = cur.execute(statement).fetchall()
        if len(results) < 1:
            return False
        return results[0]

    def get_all_buy_orders(self):
        cur = self.con.cursor()
        results = cur.execute("SELECT * FROM buyorders").fetchall()
        if len(results) < 1:
            return False
        return results

    def save_bought_item(self, item, float):
        cur = self.con.cursor()
        result = self.get_buy_order(item.url, float)
        if not result:
            return False
        bought = result[1]
        bought -= 1
        self.delete_listing_by_id(item.id)
        statement = "UPDATE buyorders set number=%s where (item='%s' and maxfloat=%s)"%(bought, item.url, float)
        cur.execute(statement)
        self.con.commit()
        return True

