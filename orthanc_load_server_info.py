import json

def get_orthanc_credentials(file_path: str) -> tuple[str, tuple[str, str]]:
    """
    Read in a JSON file from file_path and return a tuple containing the server url, username, and
    password to connect to Orthanc.

    Parameters
    ----------
    file_path : path to the JSON file containing the Orthanc credentials
    """
    with open(file_path, 'r') as json_file:
        json_data = json.load(json_file)
    return json_data['server_url'], (json_data['username'], json_data['password'])