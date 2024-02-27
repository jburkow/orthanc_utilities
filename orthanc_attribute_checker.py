'''
Filename: orthanc_attribute_checker.py
Author(s): Jonathan Burkow, burkowjo@msu.edu, Michigan State University
Last Updated: 11/10/2022
Description: Go through all files on Orthanc server and retrieve all unique header values.
'''

import argparse
import sys
import time
from pathlib import Path
from typing import List, Tuple

import requests
from tqdm import tqdm

# Set the path to the rib_fracture_utils directory
FILE = Path(__file__).resolve()
ROOT = FILE.parents[1]
sys.path.append(str(ROOT))

from orthanc_load_server_info import get_orthanc_credentials


def parse_cmd_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--credentials_file', type=str,
                        help='Path to the file containing the server url, username, and password to connect to the Orthanc server.')
    return parser.parse_args()


def retrieve_all_attributes(orthanc_url: str, orthanc_credentials: Tuple[str, str], attribute: str) -> List[str]:
    """
    Loop through all studies/series/instances in orthanc_url and get all unique attributes.

    Parameters
    ----------
    orthanc_url : URL to either all studies, series, or instances on ORTHANC server
    orthanc_credentials : username and password for ORTHANC access
    attribute   : the DICOM header value to retrieve
    """
    all_attrs = []
    all_items = requests.get(orthanc_url, auth=orthanc_credentials).json()
    for item in tqdm(all_items, desc=f'Getting all unique {attribute}s', total=len(all_items)):
        item_info = requests.get(orthanc_url + item, auth=orthanc_credentials).json()
        # tmp_attr = dcm.StudyDescription if hasattr(dcm, attribute) else 'NA'
        tmp_attr = item_info['MainDicomTags'][f'{attribute}']
        all_attrs.append(tmp_attr)
    return list(set(all_attrs))


def main():
    """Main Function"""
    parse_args = parse_cmd_args()
    orthanc_server_url, orthanc_credentials = get_orthanc_credentials(parse_args.credentials_file)

    studies_url = orthanc_server_url + '/studies/'
    series_url = orthanc_server_url + '/series/'
    instances_url = orthanc_server_url + '/instances/'

    unique_studydesc = retrieve_all_attributes(studies_url, orthanc_credentials, 'StudyDescription')
    print('--All Unique StudyDescriptions--')
    for attr in unique_studydesc:
        print(f'{attr!r}')

    unique_seriesdesc = retrieve_all_attributes(series_url, orthanc_credentials, 'SeriesDescription')
    print('--All Unique SeriesDescriptions--')
    for attr in unique_seriesdesc:
        print(f'{attr!r}')

    unique_seriesnum = retrieve_all_attributes(series_url, orthanc_credentials, 'SeriesNumber')
    print('--All Unique SeriesNumbers--')
    for attr in unique_seriesnum:
        print(f'{attr!r}')

    unique_instancedesc = retrieve_all_attributes(instances_url, orthanc_credentials, 'InstanceNumber')
    print('--All Unique InstanceNumbers--')
    for attr in unique_instancedesc:
        print(f'{attr!r}')


if __name__ == "__main__":
    print('\nStarting execution...')
    start_time = time.perf_counter()
    main()
    elapsed = time.perf_counter() - start_time
    print('Done!')
    print(f'Execution finished in {elapsed:.3f} seconds ({time.strftime("%-H hr, %-M min, %-S sec", time.gmtime(elapsed))}).\n')
