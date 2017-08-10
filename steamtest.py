import logging
from getpass import getpass

logging.basicConfig(format='[%(asctime)s] %(levelname)s %(name)s: %(message)s', level=logging.DEBUG)

from steam import SteamClient
from steam.enums import EResult
from steam.enums.emsg import EMsg
from steam.client.gc import GameCoordinator

client = SteamClient()


# client.cm.verbose_debug = True

@client.on('error')
def print_error(result):
    print("Error:", EResult(result))


@client.on('auth_code_required')
def auth_code_prompt(is_2fa, code_mismatch):
    if is_2fa:
        code = input("Enter 2FA Code: ")
        logOnDetails.update({'two_factor_code': code})
    else:
        code = input("Enter Email Code: ")
        logOnDetails.update({'auth_code': code})

    client.login(**logOnDetails)


logOnDetails = {
    'username': input("Steam user: "),
    'password': getpass("Password: "),
}

client.login(**logOnDetails)


# OR
# client.anonymous_login()

@client.on('logged_on')
def logged_on():
    print("BOOOOOOOOOOOOOOOM HEADSHOT")
    gc = GameCoordinator(client, 730)
    print(gc)
    print(client)


msg, = client.wait_event(EMsg.ClientAccountInfo)
print("Logged on as: %s" % msg.body.persona_name)
# print "SteamID: %s" % repr(client.steamid)



client.wait_event('disconnect')
