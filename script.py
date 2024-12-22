import concurrent.futures

import requests

# URL to send requests to
url = "https://finance.danielmoessner.de/stocks/test/"

# Number of parallel requests
num_requests = 10


def fetch_url(url):
    try:
        response = requests.get(url)
        return response.status_code, response.text
    except requests.RequestException as e:
        return None, str(e)


def main():
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_requests) as executor:
        # Create a list of futures
        futures = [executor.submit(fetch_url, url) for _ in range(num_requests)]

        # Process the results as they complete
        for future in concurrent.futures.as_completed(futures):
            status_code, content = future.result()
            if status_code:
                print(f"Status Code: {status_code}")
                print(
                    f"Content: {content[:100]}..."
                )  # Print first 100 characters of the content
            else:
                print(f"Request failed: {content}")


if __name__ == "__main__":
    main()
