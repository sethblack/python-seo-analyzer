import certifi
from urllib3 import PoolManager
from urllib3 import Timeout


class Http():
    def __init__(self):
        user_agent = {'User-Agent': 'Mozilla/5.0'}
        self.http = PoolManager(
            timeout=Timeout(connect=1.0, read=2.0),
            cert_reqs='CERT_REQUIRED',
            ca_certs=certifi.where(),
            headers=user_agent
        )

    def get(self, url):
        return self.http.request('GET', url)

http = Http()
        
