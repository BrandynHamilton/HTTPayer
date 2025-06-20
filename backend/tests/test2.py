import requests
import os
from dotenv import load_dotenv

load_dotenv()

HTTPAYER_API_KEY = os.getenv('HTTPAYER_API_KEY')

if not HTTPAYER_API_KEY:
    raise ValueError("HTTPAYER_API_KEY must be set in the environment variables.")\
    
url = f"http://provider.boogle.cloud:31157/httpayer"

header = {'x-api-key':HTTPAYER_API_KEY}

payload = {
    "api_url": f"http://provider.akash-palmito.org:30862/avalanche-weather",  # replace with actual 402-enabled URL
    "method": "GET",  # or "POST"
}

print("Payload:", payload)

response = requests.post(url, json=payload, headers=header)

print("Status Code:", response.status_code)
print("Response Body:", response.text)
