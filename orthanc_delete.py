'''
Filename: orthanc_delete.py
Author(s): Jonathan Burkow, burkowjo@msu.edu, Michigan State University
Last Updated: 11/10/2022
Description: Delete all patients or annotations from the Orthanc server.
'''

import argparse
import getpass
import sys
import time
from pathlib import Path
from typing import Tuple

import requests
from tqdm import tqdm

# Set the path to the rib_fracture_utils directory
FILE = Path(__file__).resolve()
ROOT = FILE.parents[1]
sys.path.append(str(ROOT))

from orthanc_load_server_info import get_orthanc_credentials


def parse_cmd_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--type', choices=['patients', 'annotations'], required=True,
                        help='Choose whether to delete patients entirely or annotations.')
    parser.add_argument('--credentials_file', type=str,
                        help='Path to the file containing the server url, username, and password to connect to the Orthanc server.')
    return parser.parse_args()


def check_credentials(server_url) -> Tuple[bool, Tuple[str, str]]:
    """
    Checks for connection success for input credentials to Orthanc.

    Returns
    -------
    connection_status : bool
        True or False whether the username and password granted access.
    credentials : tuple
        strings of input username and password
    """
    connection_status = False
    connection_tests = 3
    while connection_tests > 0 and connection_status == 0:
        username = getpass.getpass(prompt="Orthanc Username: ")
        password = getpass.getpass(prompt="Orthanc Password: ")
        credentials = (username, password)
        if requests.get(server_url, auth=credentials).status_code == 200:
            connection_status = True
        else:
            connection_tests -= 1
            print(f"Incorrect username or password.{' Please try again.' if connection_tests > 0 else ''}\n")

    return connection_status, credentials


def delete_from_server(parse_args: argparse.ArgumentParser, server_url: str, credentials: Tuple[str, str]) -> None:
    """
    Iterates through the entire list of patients or annotations and deletes them.

    Parameters
    ----------
    parse_args  : contains what type of item to delete
    credentials : strings of input username and password
    """
    orthanc_url = server_url+('/studies/' if parse_args.type == "annotations" else '/patients/')
    orthanc_list = requests.get(orthanc_url, auth=credentials).json()
    print(f"\nBeginning {parse_args.type} deletion...")
    for _, item in tqdm(enumerate(orthanc_list), f'Deleting {parse_args.type}', len(orthanc_list)):
        item_url = orthanc_url+item+('/attachments/9999/' if parse_args.type == "annotations" else '')
        requests.delete(item_url, auth=credentials)
    print(f"All {parse_args.type} deleted.")


def main() -> None:
    """Main Function"""
    parse_args = parse_cmd_args()
    orthanc_server_url, _ = get_orthanc_credentials(parse_args.credentials_file)
    status, credentials = check_credentials(orthanc_server_url)
    if not status:
        print("\nUnable to connect to Orthanc server.")
        return

    # Prompt whether or not to delete files
    print(f"\nThis will delete all {parse_args.type} stored on the Orthanc server. WARNING: THIS CANNOT BE UNDONE!")
    prompt = input(f"If you wish to delete all {parse_args.type} from the server, type 'DELETE': ")
    if prompt == 'DELETE':
        delete_from_server(parse_args, orthanc_server_url, credentials)
    else:
        print("\nPermission not provided. Exiting without deletion.")


if __name__ == "__main__":
    print('\nStarting execution...')
    start_time = time.perf_counter()
    main()
    elapsed = time.perf_counter() - start_time
    print('Done!')
    print(f'Execution finished in {elapsed:.3f} seconds ({time.strftime("%-H hr, %-M min, %-S sec", time.gmtime(elapsed))}).\n')
