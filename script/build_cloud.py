import sys
import json
import time
from enum import Enum
import requests

class ConsoleType(Enum):
    bash = "bash"
    python27 = "python2.7"


class PythonAnyWhereConsole:

    def get_all_console(self):
        url = "https://www.pythonanywhere.com/api/v0/user/PrashantSindhe/consoles/"
        headers = {
            'Authorization': 'Token d1d33365c22118b0fa2f3ae5905ddd09a6d23e96',
        }
        response = requests.request("GET", url, headers=headers)
        return response.text

    def get_all_console_id(self):
        response = self.get_all_console()
        json_data = json.loads(response)
        console_id = []
        for single_item in json_data:
            console_id.append(single_item['id'])
        return console_id

    def delete_all_existing_console(self):
        console_list = self.get_all_console_id()
        for console in console_list:
            response = self.delete_console(console)
            if response == 204:
                print(f"Deleted console {console}: Response {response}")
            else:
                print(f"Error , Response code {response}")

    def delete_console(self, console_id):
        url = f"https://www.pythonanywhere.com/api/v0/user/PrashantSindhe/consoles/{console_id}/"
        headers = {
            'Authorization': 'Token d1d33365c22118b0fa2f3ae5905ddd09a6d23e96'
        }
        response = requests.request("DELETE", url, headers=headers)
        return response.status_code

    def create_new_console(self):
        url = "https://www.pythonanywhere.com/api/v0/user/PrashantSindhe/consoles/"

        headers = {
            'Authorization': 'Token d1d33365c22118b0fa2f3ae5905ddd09a6d23e96',
            'Content-Type': 'application/json',
        }
        payload = json.dumps({
            "executable": "/bin/bash"  # This specifies that you want a bash console
        })

        response = requests.post(url, headers=headers, data=payload)

        if response.status_code == 200:
            # Return the console ID from the response
            console_info = response.json()
            print("Created new Console")
            print(f"New Console {console_info.get("id")}")
            return console_info.get("id")
        else:
            print(f"Error creating console: {response.text}")
            return None


class BuildCloud(PythonAnyWhereConsole):

    def execute(self):
        self.delete_all_existing_console()
        console_id = self.create_new_console()
        time.sleep(10)
        self.pull_latest_changes_on_pythonanywhere(console_id=console_id)

    def pull_latest_changes_on_pythonanywhere(self, console_id):
        url = f"https://www.pythonanywhere.com/api/v0/user/PrashantSindhe/consoles/{console_id}/send_input/"

        payload = json.dumps({
            "input": "cd vegitables/vegitable/\ngit pull\npython manage.py migrate\ncd ..\ncd ..\n"
        })
        headers = {
            'Authorization': 'Token d1d33365c22118b0fa2f3ae5905ddd09a6d23e96',
            'Content-Type': 'application/json'
        }

        response = requests.request("POST", url, headers=headers, data=payload)
        if response.status_code == 200:
            print("Commands executed successfully.")
        else:
            print(f"Error sending commands: {response.text}")
            sys.exit(1)


if __name__ == "__main__":
    build = BuildCloud()
    build.execute()
