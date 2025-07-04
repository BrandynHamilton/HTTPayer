from httpayer import HttPayerClient
import json

def main(urls):

    """Test the HttPayerClient with multiple URLs.
    This function sends GET requests to the provided URLs and prints the response headers,
    status codes, and response bodies. It is designed to test the functionality of the HttPayerClient
    with multiple endpoints that are expected to return 402 Payment Required responses.

    Args:
        urls (list): A list of URLs to test with the HttPayerClient.
    
    """

    responses = []

    for url in urls:
        print(f'processing {url}...')

        client = HttPayerClient()
        response = client.request("GET", url)

        print(f'response headers: {response.headers}')  # contains the x-payment-response header
        print(f'response status code: {response.status_code}')  # should be 200 OK
        print(f'response text: {response.text}')  # contains the actual resource
        print(f'response json: {response.json()}')

        responses.append(response)

    return responses

if __name__ == "__main__":
    print(f'starting test3...')
    urls = ["http://provider.akash-palmito.org:30862/base-weather",
            "http://provider.akash-palmito.org:30862/avalanche-weather"]
    main(urls)
