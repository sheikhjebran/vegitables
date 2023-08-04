import sys
import json
import time
from enum import Enum
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager


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


class BuildCloud(PythonAnyWhereConsole):

    def execute(self):
        # self.delete_all_existing_console()
        # console_id = self.create_new_console(ConsoleType.bash)
        # print(f"NewConsole Id : {console_id}")
        # self.load_console_browser(console_id)
        self.pull_latest_changes_on_pythonanywhere(console_id=29719796)

    def load_console_browser(self, console_id):
        driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))

        # Replace 'https://example.com' with the URL of the website you want to open
        url = f"https://www.pythonanywhere.com/user/PrashantSindhe/consoles/{console_id}/"

        try:
            # Open the URL
            driver.get(url)
            driver.find_element(By.ID,"id_auth-username").send_keys("Sindhe.prashanth@gmail.com")
            driver.find_element(By.ID, "id_auth-password").send_keys("Welcome@123")
            driver.find_element(By.ID,"id_next").click()
            time.sleep(180)
        finally:
            # Close the browser after use
            driver.quit()

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
