'''
Filename: orthanc_files_info.py
Author(s): Jonathan Burkow, burkowjo@msu.edu, Michigan State University
Last Updated: 02/27/2024
Description: Print number of patients, studies, series, and instances on the Orthanc web server. Can
    also print out the number of studies with annotations with --anno flag.
'''

import argparse
import sys
import time
from pathlib import Path

import requests
from tqdm import tqdm

# Set the path to the rib_fracture_utils directory
FILE = Path(__file__).resolve()
ROOT = FILE.parents[1]
sys.path.append(str(ROOT))

from orthanc_load_server_info import get_orthanc_credentials


def parse_cmd_args():
    parser = argparse.ArgumentParser()

    parser.add_argument('--anno', action="store_true",
                        help='If true, go through every study and print out how many annotations are present.')

    parser.add_argument('--credentials_file', type=str,
                        help='Path to the file containing the server url, username, and password to connect to the Orthanc server.')

    return parser.parse_args()


def main() -> None:
    """Main Function"""
    parse_args = parse_cmd_args()
    orthanc_server_url, orthanc_credentials = get_orthanc_credentials(parse_args.credentials_file)

    # Set up URLs to each level
    patients_url = f"{orthanc_server_url}/patients/"
    studies_url = f"{orthanc_server_url}/studies/"
    series_url = f"{orthanc_server_url}/series/"
    instances_url = f"{orthanc_server_url}/instances/"

    # Pull lists for each level
    patients_list = requests.get(patients_url, auth=orthanc_credentials).json()
    studies_list = requests.get(studies_url, auth=orthanc_credentials).json()
    series_list = requests.get(series_url, auth=orthanc_credentials).json()
    instances_list = requests.get(instances_url, auth=orthanc_credentials).json()

    # Print out the length of each list
    print('Number of Patients:', len(patients_list))
    print('Number of Studies:', len(studies_list))
    print('Number of Series:', len(series_list))
    print('Number of Instances:', len(instances_list))

    if parse_args.anno:
        anno_count = sum('9999' in requests.get(studies_url + study + '/attachments/', auth=orthanc_credentials).json()
                         for study in tqdm(studies_list, desc='Counting annotated studies'))
        print('Number of Annotated Studies:', anno_count)


if __name__ == "__main__":
    print('\nStarting execution...')
    start_time = time.perf_counter()
    main()
    elapsed = time.perf_counter() - start_time
    print('Done!')
    print(f'Execution finished in {elapsed:.3f} seconds ({time.strftime("%-H hr, %-M min, %-S sec", time.gmtime(elapsed))}).\n')
