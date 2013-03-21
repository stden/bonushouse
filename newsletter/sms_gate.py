import urllib2
import urllib
import base64
import sys

class Gate:
    """class for using smsbliss.ru service via GET requests"""

    __host = 'gate.smsbliss.ru'

    def __init__(self, api_login, api_password):
        self.login = api_login
        self.password = api_password

    def __sendRequest(self, uri, params=None):
        url = self.__getUrl(uri, params)
        request = urllib2.Request(url)
        passman = urllib2.HTTPPasswordMgrWithDefaultRealm()
        passman.add_password(None, url, self.login, self.password)
        authhandler = urllib2.HTTPBasicAuthHandler(passman)
        try:
            opener = urllib2.build_opener(authhandler)
            data = opener.open(request).read()
            return data
        except IOError, e:
            return e.code

    def __getUrl(self, uri, params=None):
        url = "http://%s/%s/" % (self.getHost(), uri)
        paramStr = ''
        if params is not None:
            for k, v in params.items():
                if v is None:
                    del params[k]
            paramStr = urllib.urlencode(params)
        return "%s?%s" % (url, paramStr)

    def getHost(self):
        """Return current requests host """
        return self.__host

    def setHost(self, host):
        """Changing default requests host """
        self.__host = host

    def send(self, phone, text, sender='SmsBliss',
             statusQueueName=None, scheduleTime=None, wapurl = None):
        if self.credits() > 0:
            text = text.encode('utf-8')
            """Sending sms """
            params = {'phone': phone,
                      'text': text,
                      'sender': sender,
                    'statusQueueName': statusQueueName,
                    'scheduleTime': scheduleTime,
                    'wapurl': wapurl
            }
            return self.__sendRequest('send', params)
        else:
            return 'not enough credits'

    def status(self, id):
        """Retrieve sms status by it's id """
        params = {'id': id}
        return self.__sendRequest('status', params)

    def statusQueue(self, statusQueueName, limit = 5):
        """Retrieve latest statuses from queue """
        params = {'statusQueueName': statusQueueName, 'limit': limit}
        return self.__sendRequest('statusQueue', params)

    def credits(self):
        """Retrieve current credit balance """
        result = self.__sendRequest('credits')
        if 'credits=' in result:
            return int(result[8:])

    def senders(self):
        """Retrieve available signs """
        return self.__sendRequest('senders')



if __name__ == "__main__":
    print Gate.__doc__