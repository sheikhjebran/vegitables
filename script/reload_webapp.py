import requests
import sys
url = "https://www.pythonanywhere.com/api/v0/user/mbillingtool/webapps/mbillingtool.pythonanywhere.com/reload/"

payload = {}
headers = {
  'Authorization': 'Token f604c16eae7a29e30c55fb03901a32d32a815571'
}

response = requests.request("POST", url, headers=headers, data=payload)

print(response.text)
if response.status_code != 200:
    sys.exit(1)