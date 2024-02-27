'''
Filename: orthanc_lists_to_annotate.py
Author(s): Jonathan Burkow, burkowjo@msu.edu, Michigan State University
Last Updated: 07/12/2023
Description: Accesses the Orthanc server and outputs Excel files with direct URLs to studies in the
    server. Output is either a single file with all URLs or split into separate Excel files of a
    specified length of URLs.

    Split files have number of rows <= to the chunk_size argument.

Usage: python orthanc_lists_to_annotate.py --output_type split --by series --chunk_size 50 --match_name anon_ib --filename_full <name_of_file.xlsx>
                                                          full       study                              matched
'''

import argparse
import math
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import requests
from tqdm import tqdm

# Set the path to the rib_fracture_utils directory
FILE = Path(__file__).resolve()
ROOT = FILE.parents[1]
sys.path.append(str(ROOT))

from args import ARGS
from orthanc_load_server_info import get_orthanc_credentials


def parse_cmd_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output_type', choices=['full', 'split'], required=True,
                        help='Choose whether to output a single, full list or split into multiple batches.')
    parser.add_argument('--by', choices=['study', 'series'], default="study",
                        help='Choose whether to search by study or series for getting URLs.')
    parser.add_argument('--chunk_size', type=int, default=50,
                        help='The batch size of each annotation list to split into.')
    parser.add_argument('--match_name', type=str, default='',
                        help='String to match within PatientName field.')
    parser.add_argument('--filename_full', type=str, default='Osimis_Annotations.xlsx',
                        help='Filename to save the single, full list as.')
    parser.add_argument('--credentials_file', type=str, required=True,
                        help='Path to the file containing the server url, username, and password to connect to the Orthanc server.')
    parser_args = parser.parse_args()
    if parser_args.output_type == "full" and parser_args.match_name is None:
        parser.error('Please specify --name <string> to match patient names to (e.g., anon_ib or fracture_unknown).')

    return parser_args


def split_intervals(full_df: pd.DataFrame, chunk_size: int) -> range:
    """
    Return a list of intervals to split the DataFrame `full_df` (containing all Patient IDs and Web
    Viewer URLs) into multiple DataFrames of size `chunk_size`.

    Parameters
    ----------
    full_df    : the entire list of DICOM series on Osimis server
    chunk_size : number of rows for each split DataFrame
    """
    return range(chunk_size, math.ceil(full_df.shape[0] / chunk_size) * chunk_size, chunk_size)


def pull_urls_from_orthanc(
        server_url: str,
        credentials: tuple[str, str],
        item_type: str,
        name_restriction: str
    ) -> pd.DataFrame:
    """
    Return a DataFrame of all Patient IDs, Patient Names, and Web URLs for all series/studies in the
    Orthanc server.

    Parameters
    ----------
    server_url       : url to the Orthanc server
    credentials      : username and password to connect to Orthanc server
    studies_url      : url to the studies in Orthanc
    series_url       : url to the series in Orthanc
    item_type        : whether to pull from `series` or `study`
    name_restriction : substring (e.g., `anon_ib` or `fracture_unknown`) to restrict the search
    """
    # Define URLs for each piece of DICOM files
    studies_url = f"{server_url}/studies/"
    series_url = f"{server_url}/series/"

    # Create an empty DataFrame to save information into
    list_df = pd.DataFrame(columns=['Patient ID', 'Patient Name', 'Web Viewer URL'])

    # Loop through all studies/series and get Patient IDs, names, and web viewer URLs
    all_items = requests.get(studies_url, auth=credentials).json() if item_type == "study" else requests.get(series_url, auth=credentials).json()
    for item in tqdm(all_items, desc=f'Getting {item_type} URLs', total=len(all_items)):
        series_info = requests.get(series_url + item, auth=credentials).json() if item_type == "series" else ""
        study_url = studies_url + item if item_type == "study" else studies_url + series_info['ParentStudy']
        study_info = requests.get(study_url, auth=credentials).json()
        patient_id = study_info['PatientMainDicomTags']['PatientID']
        patient_name = study_info['PatientMainDicomTags']['PatientName']
        if name_restriction.casefold() not in patient_name.casefold():
            continue
        web_viewer_url = f"{server_url}osimis-viewer/app/index.html?{item_type}={item}"
        list_df = pd.concat([list_df, pd.DataFrame({'Patient ID' : [patient_id], 'Patient Name' : [patient_name], 'Web Viewer URL' : [web_viewer_url]})], ignore_index=True)
    return list_df


def main() -> None:
    """Main Function"""
    parse_args = parse_cmd_args()
    orthanc_server_url, orthanc_credentials = get_orthanc_credentials(parse_args.credentials_file)

    # Create DataFrame of Patient IDs, names, and web viewer URLs
    list_df = pull_urls_from_orthanc(orthanc_server_url, orthanc_credentials, parse_args.by, parse_args.match_name)

    # If output_type == `full`, output entire list_df to an Excel file.
    if parse_args.output_type == "full":
        print('Writing to file...')
        list_df.to_excel(parse_args.filename_full, index=False)
        return

    # If type == `split`, shuffle `list_df` and split into multiple Excel files based on `chunk_size`.
    random_df = list_df.sample(frac=1, random_state=ARGS['RANDOM_SEED']).reset_index(drop=True)

    # Define the intervals to split the DataFrame
    interval = split_intervals(random_df, parse_args.chunk_size)

    # Split the DataFrame based on the interval
    split_dfs = np.split(random_df, interval)

    # Save the split DataFrames to unique CSV files
    print('Writing to files...')
    for i, df in enumerate(split_dfs):
        # * Change this line if creating lists for different data
        filename = f"Osimis_Annotation{'_' + parse_args.match_name if parse_args.match_name != '' else ''}_Batch_{i+1}.xlsx"
        df.to_excel(filename, index=False)


if __name__ == "__main__":
    print('\nStarting execution...')
    start_time = time.perf_counter()
    main()
    elapsed = time.perf_counter() - start_time
    print('Done!')
    print(f'Execution finished in {elapsed:.3f} seconds ({time.strftime("%-H hr, %-M min, %-S sec", time.gmtime(elapsed))}).\n')
