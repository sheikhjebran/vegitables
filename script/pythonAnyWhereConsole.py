import json
from enum import Enum

import requests


class ConsoleType(Enum):
    bash = "bash"
    python27 = "python2.7"


class PythonAnyWhereConsole:

    def getAllConsole(self):
        url = "https://www.pythonanywhere.com/api/v0/user/PrashantSindhe/consoles/"

        payload = {}
        headers = {
            'Authorization': 'Token d1d33365c22118b0fa2f3ae5905ddd09a6d23e96',
        }

        response = requests.request("GET", url, headers=headers, data=payload)

        return response.text

    def get_all_console_id(self):
        response = self.getAllConsole()
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

        payload = {}
        headers = {
            'Authorization': 'Token d1d33365c22118b0fa2f3ae5905ddd09a6d23e96'
        }

        response = requests.request("DELETE", url, headers=headers, data=payload)

        return response.status_code

    def create_new_console(self, console_type: ConsoleType):
        url = "https://www.pythonanywhere.com/api/v0/user/PrashantSindhe/consoles/"

        payload = json.dumps({
            "executable": console_type.value
        })
        headers = {
            'Authorization': 'Token d1d33365c22118b0fa2f3ae5905ddd09a6d23e96',
            'Content-Type': 'application/json',
        }

        response = requests.request("POST", url, headers=headers, data=payload)
        json_data = json.loads(response.text)
        return json_data['id']
