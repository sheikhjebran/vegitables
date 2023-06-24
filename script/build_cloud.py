import requests
import json

url = "https://www.pythonanywhere.com/api/v0/user/PrashantSindhe/consoles/29229942/send_input/"

payload = json.dumps({
  "input": "cd vegitables/vegitable/\ngit pull\npython manage.py migrate\n"
})
headers = {
  'Authorization': 'Token d1d33365c22118b0fa2f3ae5905ddd09a6d23e96',
  'Content-Type': 'application/json',
  'Cookie': 'csrftoken=B21Nk06BafyezgxCDz4NCrdydzoOmqnxCmLDjNeqpanQavzumryFMXxWUbHqRt9s; sessionid=8ri3fosi6dtepsvvz306d00e62f02085'
}

response = requests.request("POST", url, headers=headers, data=payload)

print(response.text)
