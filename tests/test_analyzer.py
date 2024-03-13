from seoanalyzer import analyze

def test_print_output():
    output = analyze('https://www.sethserver.com/tests/utf8.html')

    assert len(output['pages']) == 1
    assert output['pages'][0]['url'] == 'https://www.sethserver.com/tests/utf8.html'
    assert output['pages'][0]['title'] == 'unicode chara¢ters'
    assert output['pages'][0]['description'] == ''
    assert output['pages'][0]['word_count'] == 493
    assert output['errors'] == []
    assert output['duplicate_pages'] == []
