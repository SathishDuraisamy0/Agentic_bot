import requests

topic = "Albert Einstein"
url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{topic.replace(' ', '_')}"
resp = requests.get(url, timeout=10)

print("Status Code:", resp.status_code)
print("Content-Type:", resp.headers.get("Content-Type"))
print("Response (first 300 chars):")
print(resp.text[:300])

