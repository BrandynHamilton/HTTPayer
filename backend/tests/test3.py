import requests

r = requests.get("http://app.httpayer.com/health")
r.raise_for_status()
print(r.text)