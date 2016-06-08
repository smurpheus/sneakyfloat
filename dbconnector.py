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

    def get_deal_by_name(self, name):
        cur = self.con.cursor()
        results = cur.execute("SELECT * from deals WHERE name='%s'" % name).fetchall()
        if len(results) < 1:
            return False
        result = results[0]
        result_dict = {}
        result_dict['name'] = result[0]
        result_dict['id'] = result[1]
        return result_dict

    def get_deal_by_id(self, id):
        cur = self.con.cursor()
        results = cur.execute("SELECT * from deals WHERE id='%s'" % id).fetchall()
        if len(results) < 1:
            return False
        result = results[0]
        result_dict = {}
        result_dict['name'] = result[0]
        result_dict['id'] = result[1]
        return result_dict

    def get_all_deals(self):
        cur = self.con.cursor()
        results = cur.execute("SELECT * from deals").fetchall()
        if len(results) < 1:
            return False
        result = []
        for each in results:
            result_dict = {}
            result_dict['name'] = each[0]
            result_dict['id'] = each[1]
            result.append(result_dict)
        return result

    def get_all_grps(self):
        cur = self.con.cursor()
        results = cur.execute("SELECT * from buygroup").fetchall()
        if len(results) < 1:
            return False
        result = []
        for each in results:
            result_dict = {}
            result_dict['grp_id'] = each[0]
            result_dict['number'] = each[1]
            result_dict['float'] = each[2]
            result_dict['deal_id'] = each[3]
            result_dict['price'] = each[4]
            result.append(result_dict)
        return result

    def get_deal_grp_by(self, key, value):
        cur = self.con.cursor()
        results = cur.execute("SELECT * from buygroup WHERE %s='%s'" %(key, value)).fetchall()
        if len(results) < 1:
            return False
        result = results[0]
        result_dict = {}
        result_dict['grp_id'] = result[0]
        result_dict['number'] = result[1]
        result_dict['float'] = result[2]
        result_dict['deal_id'] = result[3]
        result_dict['price'] = result[4]
        return result_dict

    def create_deal_grp(self, grp_id, number, floatv, deal_id, price):
        statement = "INSERT INTO buygroup VALUES(%s,%s,%s,%s,%s)" % (grp_id, number, floatv, deal_id, price)
        cur = self.con.cursor()
        cur.execute(statement)
        self.con.commit()

    def create_deal(self, name):
        alldeals = self.get_all_deals()
        if alldeals:
            max_id = max(x[0] for x in alldeals)
            max_id += 1
        else:
            max_id = 0
        names = [x for x in alldeals if x[1] == name]
        if names < 1:
            statement = "INSERT INTO deals VALUES(%s,'%s')" % (name, max_id)
            cur = self.con.cursor()
            cur.execute(statement)
            self.con.commit()
            return True
        return False

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

    def create_buy_order(self, item, grp_id):
        result = self.get_buy_order(item, grp_id)
        if result:
            return False
        statement = "INSERT INTO buyorders VALUES ('%s', %s)" % (item, grp_id)
        print(statement)
        cur = self.con.cursor()
        cur.execute(statement)
        self.con.commit()

    def get_buy_order_by(self, key, value):
        cur = self.con.cursor()
        statement = "SELECT * FROM buyorders where %s='%s'" % (key, value)
        results = cur.execute(statement).fetchall()
        if len(results) < 1:
            return False

        return {'item': results[0][0], 'buygrp':results[0][1]}

    def get_all_buy_orders(self):
        cur = self.con.cursor()
        results = cur.execute("SELECT * FROM buyorders").fetchall()
        if len(results) < 1:
            return False
        result = []
        for r in results:
            b = {}
            b['item']=r[0]
            b['buygrp'] = r[1]
        return result

    def get_deals_as_dict(self):

        deal_dict = {}
        all_grps = self.get_all_grps()
        allbuyorders = self.get_all_buy_orders()
        all_deals = self.get_all_deals()
        if all_grps:
            grp_dict = {}
            for grp in all_grps:
                grp_dict[grp['grp_id']] = {'number': grp['number'],
                                 'float': grp['float'],
                                 'price': grp['price'],
                                 'items': [],
                                 'deal_id': grp['deal_id']}
            if allbuyorders:
                for buyorder in allbuyorders:
                    grp_dict[buyorder['buygrp']]['items'].append(buyorder['item'])


            if all_deals:
                for deal in all_deals:
                    filtered = {key:value for key, value in grp_dict.iteritems() if value['deal_id'] == deal['id']}
                    deal_dict[deal['id']] = {'name': deal['name'],
                                             'groups': filtered}
        return deal_dict






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

