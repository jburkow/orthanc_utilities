'''
Filename: orthanc_list_annotated_images.py
Author(s): Jonathan Burkow, burkowjo@msu.edu, Michigan State University
Last Updated: 11/10/2022
Description: Accesses the ORthanc server to create an Excel file containing Patient IDs and URL
    links to all images that have been annotated.
'''

import argparse
import sys
import time
from pathlib import Path

import pandas as pd
import requests
from tqdm import tqdm

# Set the path to the rib_fracture_utils directory
FILE = Path(__file__).resolve()
ROOT = FILE.parents[1]
sys.path.append(str(ROOT))

from orthanc_load_server_info import get_orthanc_credentials


def parse_cmd_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--filename', type=str, default='annotated_images_list.xlsx',
                        help='Name of the Excel file to save to.')
    parser.add_argument('--credentials_file', type=str,
                        help='Path to the file containing the server url, username, and password to connect to the Orthanc server.')
    return parser.parse_args()


def pull_urls_from_orthanc(
        studies_url: str,
        studies_list: list[str],
        orthanc_server_url: str,
        orthanc_credentials: tuple[str, str]
    ) -> pd.DataFrame:
    """
    Return a DataFrame of Patient IDs, Patient Names, and Web URLs for all annotated studies in the
    Orthanc server.

    Parameters
    ----------
    studies_url         : url to the studies in Orthanc
    studies_list        : list of all annotated studies in Orthanc
    orthanc_credentials : username and password to connect to Orthanc server
    """
    info_df = pd.DataFrame(columns=['Patient ID', 'Patient Name', 'Web Viewer URL'])

    # Loop through all studies containing annotations and add information to info_df
    for study in tqdm(studies_list, desc="Storing annotated Patient IDs, Names, and Orthanc URLs"):
        # Retrieve the information from the study
        study_info = requests.get(studies_url + study, auth=orthanc_credentials).json()
        patient_id = study_info['PatientMainDicomTags']['PatientID']
        patient_name = study_info['PatientMainDicomTags']['PatientName']
        web_viewer_url = orthanc_server_url + 'osimis-viewer/app/index.html?study=' + study
        temp_df = pd.DataFrame({'Patient ID' : [patient_id], 'Patient Name' : [patient_name], 'Web Viewer URL' : [web_viewer_url]})
        info_df = pd.concat([info_df, temp_df], ignore_index=True)

    return info_df


def main() -> None:
    """Main Function"""
    parse_args = parse_cmd_args()
    orthanc_server_url, orthanc_credentials = get_orthanc_credentials(parse_args.credentials_file)

    studies_url = orthanc_server_url + 'studies/'  # URL for the uploaded studies

    # Make a list of all studies on Orthanc database
    all_studies = requests.get(studies_url, auth=orthanc_credentials).json()
    studies_list = [study for study in all_studies if '9999' in requests.get(studies_url + study + '/attachments/', auth=orthanc_credentials).json()]

    # Print out number of annotated studies
    print(f'\n{len(studies_list)} studies have been annotated.\n')

    # Create an empty DataFrame to add IDs, Names, and URLs to
    annotated_df = pull_urls_from_orthanc(studies_url, studies_list, orthanc_server_url, orthanc_credentials)

    # Save the dataframe to an Excel file
    print('Writing to file...')
    annotated_df.to_excel(parse_args.filename, index=False)


if __name__ == "__main__":
    print('\nStarting execution...')
    start_time = time.perf_counter()
    main()
    elapsed = time.perf_counter() - start_time
    print('Done!')
    print(f'Execution finished in {elapsed:.3f} seconds ({time.strftime("%-H hr, %-M min, %-S sec", time.gmtime(elapsed))}).\n')
