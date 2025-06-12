from httpayer import HttPayerClient

client = HttPayerClient()
response = client.request("GET", "http://localhost:4021/weather")

print(response.headers)  # contains the x-payment-response header
print(response.status_code)  # should be 200 OK
print(response.text)  # contains the actual resource
print(response.json())
