import urllib.request
import json

URL = "https://wdixxgldo6nkydfcncocpvdqu40ukjkt.lambda-url.us-east-1.on.aws/api/memories"

def run_test():
    print(f"Sending POST to {URL}...")
    req = urllib.request.Request(
        URL,
        data=b"{}",
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            res_body = response.read().decode("utf-8")
            data = json.loads(res_body)
            print("Success!")
            print(json.dumps(data, indent=2))
    except urllib.error.HTTPError as e:
        print(f"HTTP Error: {e.code} {e.reason}")
        print(e.read().decode("utf-8"))
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    run_test()
