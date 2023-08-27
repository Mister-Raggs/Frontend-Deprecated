from apps.common import utils, constants
from apps.common.custom_exceptions import MissingFolderException


def check_and_process_blob():
    """
    check_and_process_blob _summary_
    """
    input_blobs_list = []
    company_blobs_list = [
        path.name
        for path in utils.default_blob_container_client().list_blobs(
            name_starts_with=constants.COMPANY_ROOT_FOLDER_PREFIX
        )
    ]

    if len(company_blobs_list) == 0:
        raise MissingFolderException(f"Folders with prefix '{constants.COMPANY_ROOT_FOLDER_PREFIX}' do not exist ")

    incoming_blobs_list = [item for item in company_blobs_list if constants.DEFAULT_INCOMING_SUBFOLDER in item]
    if len(incoming_blobs_list) == 0:
        raise MissingFolderException(f"'{constants.DEFAULT_INCOMING_SUBFOLDER}' folders do not exist.")

    incoming_blobs_list = [item for item in incoming_blobs_list if "dummy" not in item.lower()]
    for incoming_blob in incoming_blobs_list:
        input_blobs_list.append(blob_validator(incoming_blob))

    filtered_list = [item for item in input_blobs_list if item is not None]
    for blob_path in filtered_list:
        copy_blob_to_validation_successful(blob_path, constants.DEFAULT_VALIDATION_SUCCESSFUL_SUBFOLDER)

    validation_failed_list = [item for item in incoming_blobs_list if item not in filtered_list]
    for blob_path in validation_failed_list:
        copy_blob_to_validation_successful(blob_path, constants.DEFAULT_VALIDATION_FAILED_SUBFOLDER)


def blob_validator(blobpath: str):
    """
    blob_validator _summary_

    Args:
        blobpath (str): _description_

    Returns:
        _type_: _description_
    """
    blob_client = utils.default_blob_container_client().get_blob_client(blobpath)
    properties = blob_client.get_blob_properties()

    if properties.size <= 5000000:
        if not (
            "exe" in properties.name.lower()
            or "bat" in properties.name.lower()
            or "com" in properties.name.lower()
            or "cmd" in properties.name.lower()
            or "inf" in properties.name.lower()
            or "ipa" in properties.name.lower()
            or "osx" in properties.name.lower()
            or "pif" in properties.name.lower()
            or "run" in properties.name.lower()
            or "wsh" in properties.name.lower()
        ):
            return blobpath


def copy_blob_to_validation_successful(blob_path: str, destination_folder: str):
    """
    copy_blob_to_validation_successful _summary_

    Args:
        blob_path (str): _description_
        destination_folder (str): _description_
    """
    destination_blob_path = blob_path.replace(constants.DEFAULT_INCOMING_SUBFOLDER, destination_folder)
    source_blob_client = utils.default_blob_container_client().get_blob_client(blob=blob_path)
    destination_blob_client = utils.default_blob_container_client().get_blob_client(blob=destination_blob_path)
    destination_blob_client.start_copy_from_url(source_blob_client.url)
    source_blob_client.delete_blob()
