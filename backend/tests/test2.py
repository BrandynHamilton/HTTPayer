import requests

url = "http://localhost:3000/httpayer"

payload = {
    "api_url": "http://localhost:4021/weather",  # replace with actual 402-enabled URL
    "method": "GET",  # or "POST"
}

response = requests.post(url, json=payload)

print("Status Code:", response.status_code)
print("Response Body:", response.text)
