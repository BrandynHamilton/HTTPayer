import requests

r = requests.get("http://provider.akash-palmito.org:30862/health")
r.raise_for_status()
print(r.text)