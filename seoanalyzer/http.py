import certifi
import urllib3


class Http():
    def __init__(self):
        self.http = urllib3.PoolManager(
            timeout=urllib3.Timeout(connect=1.0, read=2.0),
            cert_reqs='CERT_REQUIRED',
            ca_certs=certifi.where()
        )

    def get(self, url):
        return self.http.request('GET', url)

http = Http()
        