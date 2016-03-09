import requests, json
overview_base_url = "http://steamcommunity.com/market/priceoverview/?country=DE&currency=3&appid=730&market_hash_name="
market_listing_base_url = "http://steamcommunity.com/market/listings/730/"
listing_manipulator = "/render?start=%s&count=%s&currency=3&language=german&format=json&sort=price"

item_link = raw_input("Gib mir link!:")
extracted_item = item_link.split("/")[-1]
print extracted_item
priceoverview_url = item_link + listing_manipulator%(0,1)
print priceoverview_url
r = requests.get(priceoverview_url)
print type(r.json()["total_count"])
vol = int(r.json()["total_count"]) /10
print vol
pages = range(0,vol,100)
for each in pages:
    start = each
    count = 100
    if pages.index(each) == len(pages) - 1:
        count = vol % 100
    listing_url = item_link + listing_manipulator%(start, count)
    print listing_url
    print start
    print count
    r = requests.get(listing_url)
    data = r.json()
    for key, value in data['listinginfo'].iteritems():
        print "ID: %s" % key
        print "asset_id : %s" % value['asset']['id']
        print value['asset']['market_actions'][0]['link'].split("%assetid%")[-1]
        print value['asset']['market_actions'][0]['link'].replace("%listingid%", key).replace("%assetid%", value['asset']['id'])
        if "converted_price" in value.keys() and "converted_fee" in value.keys():
            print str(float(value["converted_price"]) + float(value["converted_fee"]))
        else:
            print str(float(value["price"]) + float(value["fee"]))
    #print r.json()