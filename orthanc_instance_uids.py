'''
Filename: orthanc_instance_uids.py
Author(s): Jonathan Burkow, burkowjo@msu.edu, Michigan State University
Last Updated: 11/10/2022
Description: Accesses Orthanc server to create a CSV file listing all InstanceUIDs of annotated
    instances that can be used to crop and process the proper annotated images.
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

from args import ARGS
from orthanc_load_server_info import get_orthanc_credentials


def parse_cmd_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--ignore_str',
                        help='If used, skips any patients where PatientID contains ignore_str.')
    parser.add_argument('--credentials_file', type=str,
                        help='Path to the file containing the server url, username, and password to connect to the Orthanc server.')

    return parser.parse_args()


def extract_annotated_studies(orthanc_credentials: tuple[str, str],
                              studies_url: str,
                              series_url: str,
                              instances_url: str,
                              ignore_str: str | None) -> tuple[list[str], list[str], list[str]]:
    """
    Loop through all studies on the Orthanc server to check for annotated images.

    Parameters
    ----------
    orthanc_credentials : username and password to connect to Orthanc server
    studies_url         : URL directly to list of all studies on Orthanc server
    series_url          : URL directly to list of all series on Orthanc server
    instances_url       : URL directly to list of all instances on Orthanc server
    ignore_str          : skips any patients containing ignore_str in PatientID

    Returns
    -------
    annotated_instances : list of all InstanceUIDs of annotated images
    patient_ids         : list of all PatientIDs of annotated images
    patient_names       : list of all PatientNames of annotated images
    """
    # Pull out list of all studies on the server
    all_studies = requests.get(studies_url, auth=orthanc_credentials).json()

    annotated_instances = []
    patient_ids = []
    patient_names = []
    for study in tqdm(all_studies, desc='Finding annotated studies', total=len(all_studies)):
        # Skip to next study if current study has no annotation file
        if '9999' not in requests.get(f'{studies_url}{study}/attachments/', auth=orthanc_credentials).json():
            continue

        # Go into annotation data to get instance UUIDs
        annotation_data = requests.get(f'{studies_url}{study}/attachments/9999/data', auth=orthanc_credentials).json()
        instance_uuids = [key for key in annotation_data.keys() if annotation_data.get(key)]

        for k, uuid in enumerate(instance_uuids):
            instance_uuids[k] = uuid[:-2]  # Cut off ":0" from end of each UUID

        # Retrieve information on the study to get all attached series
        study_info = requests.get(f'{studies_url}{study}', auth=orthanc_credentials).json()
        patient_id = study_info['PatientMainDicomTags']['PatientID'].replace(' ', '_')
        patient_name = study_info['PatientMainDicomTags']['PatientName'].replace(' ', '_')
        all_series = study_info['Series']

        # Skip to next study if --patient_str was used and PatientID contains ignore_str
        if ignore_str and ignore_str.lower() in patient_id.lower():
            continue

        # Loop through all series to check all instances
        # If instance is in the UUID list from annotations, save the UID to the list
        for series in all_series:
            series_info = requests.get(f'{series_url}{series}', auth=orthanc_credentials).json()

            all_instances = series_info['Instances']
            # Loop through instances to check whether UUID matches annotation
            for instance in all_instances:
                if instance not in instance_uuids:
                    continue
                instance_info = requests.get(f'{instances_url}{instance}', auth=orthanc_credentials).json()
                instance_uid = instance_info['MainDicomTags']['SOPInstanceUID']
                annotated_instances.append(instance_uid)
                patient_ids.append(patient_id)
                patient_names.append(patient_name)

    return annotated_instances, patient_ids, patient_names


def main() -> None:
    """Main Function"""
    parse_args = parse_cmd_args()
    orthanc_server_url, orthanc_credentials = get_orthanc_credentials(parse_args.credentials_file)

    # Define URLs for studies, series, and instances
    studies_url = orthanc_server_url + '/studies/'
    series_url = orthanc_server_url + '/series/'
    instances_url = orthanc_server_url + '/instances/'

    annotated_instances, patient_ids, patient_names = extract_annotated_studies(orthanc_credentials,
                                                                                studies_url,
                                                                                series_url,
                                                                                instances_url,
                                                                                parse_args.ignore_str)

    # Save the list of UIDs to file
    print('Writing to file...')
    with open(ARGS['INSTANCE_UID_FILENAME'], 'w') as out_file:
        for uid, patient_id, name in zip(annotated_instances, patient_ids, patient_names):
            out_str = ','.join([str(uid), str(patient_id), str(name)]) + '\n'
            out_file.write(out_str)


if __name__ == "__main__":
    print('\nStarting execution...')
    start_time = time.perf_counter()
    main()
    elapsed = time.perf_counter() - start_time
    print('Done!')
    print(f'Execution finished in {elapsed:.3f} seconds ({time.strftime("%-H hr, %-M min, %-S sec", time.gmtime(elapsed))}).\n')
