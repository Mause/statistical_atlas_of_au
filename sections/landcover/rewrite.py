from lxml.etree import fromstring

with open('pa_luav4g9abl07811a00.xml', 'rb') as fh:
    xml = fromstring(fh.read())


import IPython
IPython.embed()

# char_strings = xml.xpath('.//gco:CharacterString', namespaces={'gco': 'https://gc.gov.a'})
# from pprint import pprint
# pprint(list(char_strings))
