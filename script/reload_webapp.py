import os
import sys
import requests


def main() -> int:
  username = os.getenv("PYTHONANYWHERE_USERNAME", "mbillingtool")
  webapp_domain = os.getenv("PYTHONANYWHERE_WEBAPP", f"{username}.pythonanywhere.com")
  api_token = os.getenv("PYTHONANYWHERE_API_TOKEN")

  if not api_token:
    print("Error: missing PYTHONANYWHERE_API_TOKEN environment variable")
    return 1

  url = f"https://www.pythonanywhere.com/api/v0/user/{username}/webapps/{webapp_domain}/reload/"
  headers = {'Authorization': f'Token {api_token}'}

  response = requests.post(url, headers=headers, data={})
  print(response.text)
  return 0 if response.status_code == 200 else 1


if __name__ == "__main__":
  sys.exit(main())