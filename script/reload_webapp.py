import requests
import sys
url = "https://www.pythonanywhere.com/api/v0/user/PrashantSindhe/webapps/PrashantSindhe.pythonanywhere.com/reload/"

payload = {}
headers = {
  'Authorization': 'Token d1d33365c22118b0fa2f3ae5905ddd09a6d23e96'
}

response = requests.request("POST", url, headers=headers, data=payload)

print(response.text)
if response.status_code != 200:
    sys.exit(1)