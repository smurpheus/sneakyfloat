import sys
import imaplib
import getpass
import email
import email.header
import datetime

EMAIL_FOLDER = "Steam"




class EmailConnector(object):

    def __init__(self, email, passwd=None, server='imap.gmail.com'):
        self.imapsock = imaplib.IMAP4_SSL(server)
        self.email = email
        if passwd is None:
            self.passwd = getpass.getpass()
        else:
            self.passwd = passwd
        try:
            rv, data = self.imapsock.login(self.email, self.passwd)
        except imaplib.IMAP4.error:
            print "LOGIN FAILED!!! "



    def __exit__(self, exc_type, exc_value, traceback):
        self.imapsock.logout()

    def process_mailbox(self):
        """
        Do something with emails messages in the folder.
        For the sake of this example, print some headers.
        """
        emails_by_date = {}

        rv, data = self.imapsock.search(None, "ALL")
        if rv != 'OK':
            print "No messages found!"
            return

        if isinstance(data[0], str):
            for num in data[0].split():
                rv, raw_data = self.imapsock.fetch(num, '(RFC822)')
                if rv != 'OK':
                    print "ERROR getting message", num
                    return

                msg = email.message_from_string(raw_data[0][1])
                content = raw_data[0][1]
                decode = email.header.decode_header(msg['Subject'])[0]
                subject = unicode(decode[0])
                print 'Message %s: %s' % (num, subject)
                # Now convert to local date-time
                date_tuple = email.utils.parsedate_tz(msg['Date'])
                if date_tuple:
                    timestamp = email.utils.mktime_tz(date_tuple)
                    emails_by_date[timestamp] = content
                    local_date = datetime.datetime.fromtimestamp(
                        email.utils.mktime_tz(date_tuple))
                    print "Local Date:", \
                        local_date.strftime("%a, %d %b %Y %H:%M:%S")
        return emails_by_date

    def _get_code(self, msg):
        querystring = "Guard-Code:"
        position = msg.find(querystring)
        position += len(querystring)
        return msg[position:position+7].replace("\r","").replace("\n","")

    def getNewestCode(self):
        rv, data = self.imapsock.select(EMAIL_FOLDER)
        if rv == 'OK':
            print "Processing mailbox...\n"
            mails = self.process_mailbox()
            newest = max(mails.keys())
            self.imapsock.close()
            return self._get_code(mails[newest])
        else:
            print "ERROR: Unable to open mailbox ", rv


if __name__ == "__main__":
    emailaddr = raw_input("Bitte Email Adresse eingeben: ")
    ec = EmailConnector(emailaddr)
    print ec.getNewestCode()
