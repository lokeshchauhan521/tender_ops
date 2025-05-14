

import requests

import urllib.parse

token = "0bfa522019bf452fba462a89e207635182992e2b92d"

# url = "https://eprocure.gov.in/cppp/latestactivetendersnew/mmpdata"
url = "https://etender.up.nic.in/nicgep/app?page=FrontEndTenderDetailsExternal&service=page&tnid=1879374"

targetUrl = urllib.parse.quote(url)

url = "http://api.scrape.do/?token={}&url={}".format(token, targetUrl)

response = requests.request("GET", url)

with open("tender.pdf" , "wb" ) as dt:
    dt.write(response.content)