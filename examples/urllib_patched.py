from geventhttpclient import httplib
httplib.patch()

from urllib.request import urlopen


print(urlopen('https://www.google.fr/').read())


