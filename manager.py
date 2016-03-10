__author__ = 'smurpheus'
from getpass import getpass
from steam import SteamClient
from steam.enums import EResult
from steam.enums.emsg import EMsg
from steam.client.gc import GameCoordinator
from listing_manager import Listing
from steam.core.msg import GCMsgHdr, GCMsgHdrProto
from steam.protobufs.cstrike15_gcmessages_pb2 import CMsgGCCStrike15_v2_Client2GCEconPreviewDataBlockRequest as PrevMsg
from steam.protobufs.cstrike15_gcmessages_pb2 import k_EMsgGCCStrike15_v2_Client2GCEconPreviewDataBlockRequest as RequestNUm
import requests

class Manager(object):
    def __init__(self):
        self.logOnDetails = {
                'username': raw_input("Steam user: "),
                'password': getpass("Password: "),
            }

        client = SteamClient()
        self.client = client
        self.client.on('error', self._handle_client_error)
        self.client.on('auth_code_required', self._handle_auth_req)
        self.client.on('logged_on', self._client_handle_logon)
        self.client.login(**self.logOnDetails)
        msg, = self.client.wait_event(EMsg.ClientAccountInfo)
        print "Logged on as: %s" % msg.body.persona_name

    def _handle_client_error(self, result):
        print "Error:", EResult(result)

    def _handle_auth_req(self, is_2fa, code_mismatch):
        if is_2fa:
            code = raw_input("Enter 2FA Code: ")
            self.logOnDetails.update({'two_factor_code': code})
        else:
            code = raw_input("Enter Email Code: ")
            self.logOnDetails.update({'auth_code': code})

        self.client.login(**self.logOnDetails)

    def _client_handle_logon(self):
        print "Client logon was called!"
        self.gc = GameCoordinator(self.client, 730)
        self.gc.on(None, self._handle_gc_message)
        self.gc.on('message', self._handle_gc_message)
        msghdr = GCMsgHdrProto(4006)
        # msghdr = GCMsgHdr(4006)
        from steam.protobufs import gcsdk_gcmessages_pb2
        msg = gcsdk_gcmessages_pb2.CMsgClientHello()
        rmsg = self.gc.send(msghdr, msg.SerializeToString())
        print rmsg

    def _handle_gc_message(self, emsg, header, payload):
        print "gc got something%s  %s  %s"%(emsg,header, payload)

if __name__ == "__main__":
    m = Manager()
    r = requests.get("http://steamcommunity.com/market/listings/730/AK-47%20%7C%20Redline%20%28Field-Tested%29/render?start=0&count=1&currency=3&language=german&format=json")
    listing = r.json()['listinginfo'].values()[0]
    list = Listing(listing)
    msghdr = GCMsgHdrProto(RequestNUm)
    # msghdr = GCMsgHdr(RequestNUm)
    params = {
        "param_s": list.id,
        "param_a": list.asset_id,
        "param_d": list.d_parameter[1:],
        "param_m": "0"
    }
    print params
    msg = PrevMsg()
    msg.param_s = int(list.id)
    msg.param_a = int(list.asset_id)
    msg.param_d = int(list.d_parameter[1:])
    msg.param_m = 0
    rmsg = m.gc.send(msghdr, msg.SerializeToString())
    print "wooo msg %s" % rmsg
