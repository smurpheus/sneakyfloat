__author__ = 'smurpheus'
import sqlite3
from listing_manager import Listing
class DBConnector(object):
    def __init__(self):
        self.con = sqlite3.connect('itemstorage.db')

    def create_listing(self, listing):
        statement = "INSERT INTO listings VALUES(%s,%s,%s,'%s',%s,%s,%s,%s,%s, '%s', %s)" % (listing.id, listing.asset_id,
                                                                                listing.d_parameter, listing.name, listing.price,
                                                                                listing.total_price, listing.paintwear, listing.quality,
                                                                                listing.paintindex, listing.url, listing.fee)
        cur = self.con.cursor()
        cur.execute(statement)
        self.con.commit()

    def get_listing_by_id(self, listing_id):
        cur = self.con.cursor()
        results = cur.execute("SELECT * from listings WHERE Id=%s"%listing_id).fetchall()
        if len(results) < 1:
            return False
        result=results[0]
        return Listing(id=result[0], asset_id=result[1], d_param=result[2], name=result[3], price=result[4], total_price=result[5], paintwear=result[6], quality=result[7], paintindex=result[8], url=result[9], fee=result[10])

    def delete_listing_by_id(self, listing_id):
        cur = self.con.cursor()
        cur.execute("DELETE from listings WHERE Id=%s"%listing_id)

    def __del__(self):
        self.con.close()