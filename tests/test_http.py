from seoanalyzer import http

def test_http():
    assert http.http.get('https://www.sethserver.com/tests/utf8.html')
