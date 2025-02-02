import sys
import os
import json
import time
from enum import Enum
import requests
from typing import List, Optional


class ConsoleType(Enum):
    """Enum for specifying console types."""
    BASH = "bash"
    PYTHON_3_10 = "python3.10"


class APIClient:
    """Handles HTTP requests to the PythonAnywhere API."""

    BASE_URL = "https://www.pythonanywhere.com/api/v0/user/mbillingtool/"

    def __init__(self, api_token: str):
        self.headers = {
            'Authorization': f'Token {api_token}',
            'Content-Type': 'application/json',
        }

    def get(self, endpoint: str) -> requests.Response:
        """Send a GET request to the API."""
        return requests.get(f"{self.BASE_URL}{endpoint}", headers=self.headers)

    def post(self, endpoint: str, payload: dict) -> requests.Response:
        """Send a POST request to the API."""
        return requests.post(f"{self.BASE_URL}{endpoint}", headers=self.headers, data=json.dumps(payload))

    def delete(self, endpoint: str) -> requests.Response:
        """Send a DELETE request to the API."""
        return requests.delete(f"{self.BASE_URL}{endpoint}", headers=self.headers)


class PythonAnywhereConsole:
    """Manages PythonAnywhere consoles."""

    def __init__(self, api_client: APIClient):
        self.api_client = api_client

    def get_all_consoles(self) -> List[dict]:
        """Fetch all active consoles."""
        response = self.api_client.get("consoles/")
        response.raise_for_status()
        return response.json()

    def get_all_console_ids(self) -> List[int]:
        """Get the IDs of all active consoles."""
        return [console['id'] for console in self.get_all_consoles()]

    def delete_all_existing_consoles(self):
        """Delete all active consoles."""
        console_ids = self.get_all_console_ids()
        for console_id in console_ids:
            response = self.api_client.delete(f"consoles/{console_id}/")
            if response.status_code == 204:
                print(f"Deleted console {console_id}")
            else:
                print(f"Failed to delete console {
                      console_id}: {response.status_code}")

    def create_new_console(self, console_type: ConsoleType = ConsoleType.BASH) -> Optional[int]:
        """Create a new console."""
        payload = {"executable": f"/bin/{console_type.value}"}
        response = self.api_client.post("consoles/", payload)

        if response.status_code == 201:
            console_info = response.json()
            print(f"Created new console with ID {console_info.get('id')}")
            return console_info.get("id")
        else:
            print(f"Error creating console: {response.text}")
            return None

    def is_console_ready(self, console_id: int) -> bool:
        """Check if a console is ready to accept commands."""
        response = self.api_client.get(f"consoles/{console_id}/")
        if response.status_code == 200:
            return response.json().get('is_ready', False)
        else:
            print(f"Error checking console status: {response.text}")
            return False

    def wait_for_console_to_start(self, console_id: int, max_attempts: int = 10, delay: int = 2):
        """Wait for a console to be ready."""
        for attempt in range(max_attempts):
            if self.is_console_ready(console_id):
                print(f"Console {console_id} is ready.")
                return
            print(f"Attempt {
                  attempt + 1}/{max_attempts}: Console not ready. Retrying in {delay} seconds...")
            time.sleep(delay)

        print(f"Console {console_id} is not ready after {
              max_attempts} attempts.")
        sys.exit(1)


class BuildCloud(PythonAnywhereConsole):
    """Build and manage cloud services using PythonAnywhere consoles."""

    def execute(self):
        """Execute commands to pull latest changes and migrate database."""
        console_ids = self.get_all_console_ids()
        if console_ids:
            self.pull_latest_changes_on_pythonanywhere(
                console_id=console_ids[0])
        else:
            print("No active consoles found. Exiting.")

    def pull_latest_changes_on_pythonanywhere(self, console_id: int):
        """Send commands to a specific console."""
        payload = {"input": "cd vegitables/vegitable/\ngit pull\npython manage.py migrate\npython manage.py collectstatic --noinput\ncd ..\ncd ..\n"}
        response = self.api_client.post(
            f"consoles/{console_id}/send_input/", payload)

        if response.status_code == 200:
            print("Commands executed successfully.")
        else:
            print(f"Error sending commands: {response.text}")
            sys.exit(1)


if __name__ == "__main__":
    # Load API token from environment variables
    API_TOKEN = os.getenv("PYTHONANYWHERE_API_TOKEN")

    if not API_TOKEN:
        print("Error: API token is not set. Please set PYTHONANYWHERE_API_TOKEN environment variable.")
        sys.exit(1)

    api_client = APIClient(api_token=API_TOKEN)
    build_cloud = BuildCloud(api_client=api_client)
    build_cloud.execute()
