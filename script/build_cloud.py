import requests
import json
import sys

from script.pythonAnyWhereConsole import PythonAnyWhereConsole, ConsoleType


class BuildCloud(PythonAnyWhereConsole):

    def execute(self):
        #self.delete_all_existing_console()
        console_id = 29719296 #self.create_new_console(ConsoleType.bash)
        self.pull_latest_changes_on_pythonanywhere(console_id)

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

        print(response.text)
        if response.status_code != 200:
            sys.exit(1)


if __name__ == "__main__":
    build = BuildCloud()
    build.execute()
