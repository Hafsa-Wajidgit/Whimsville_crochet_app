import urllib.request, urllib.parse, re

url = 'http://localhost:5000/products/update/1'
data = urllib.parse.urlencode({'title': 'Test', 'category': 'Plushies', 'price': '10', 'quantity': '10'}).encode('utf-8')
req = urllib.request.Request(url, data=data)
res = urllib.request.urlopen(req)
html = res.read().decode('utf-8')

match = re.search(r'Database error: .*', html)
if match:
    print('Found error text:', match.group(0))
else:
    match2 = re.search(r'<div class="flash error">(.*?)</div>', html, re.DOTALL)
    if match2:
        print('Flash:', match2.group(1).strip())
    else:
        print('Could not find flash container')
