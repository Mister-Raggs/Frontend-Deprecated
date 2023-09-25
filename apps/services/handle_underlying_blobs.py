import logging
from typing import List
from datetime import datetime, timedelta
from azure.storage.blob import BlobServiceClient

from apps.common import utils, constants
from apps.models.input_blob_model import InputBlob, LifecycleStatus, LifecycleStatusTypes, MetaData


def check_underlying_blob_and_move():
    """
    Checks db and move blob that are more than 6hrs old in Azure Blob Storage.

    """
    blob_service_client = utils.get_azure_storage_blob_service_client()
    logging.info("getting list of underlying_blobs from Mongodb.")

    # Getting the list of blob from Incoming folder
    incoming_input_blob_list = get_list_of_input_blob_from_mongodb_in_incoming()
    if len(incoming_input_blob_list) > 0:
        logging.info("Total underlying input_blobs found in Incoming folder are %s", len(incoming_input_blob_list))
        for input_blob in incoming_input_blob_list:
            input_blob.incoming_blob_path = input_blob.incoming_blob_path.replace("\\", "/")
            input_blob.underlying_blob_path = input_blob.incoming_blob_path.replace(
                constants.DEFAULT_INCOMING_SUBFOLDER, constants.DEFAULT_UNDERLYING_SUBFOLDER
            )
            input_blob.save()
            # moving from incoming to underlying folder
            move_blob_from_source_folder_to_destination_folder_in_azure_blob_storage(
                input_blob.incoming_blob_path, input_blob.underlying_blob_path, blob_service_client
            )
            input_blob.is_underlying = True
            input_blob.is_active = False
            processing_lifecycle_status = LifecycleStatus(
                status=LifecycleStatusTypes.UNDERLYING,
                message="File is been underlyed by more than 6 hrs.",
                updated_date_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            )
            input_blob.lifecycle_status_list.append(processing_lifecycle_status)
            input_blob.save()

    # Getting the list of blob from Validation_Successful folder
    validation_input_blob_list = get_list_of_input_blob_from_mongodb_in_validation_successful()
    if len(validation_input_blob_list) > 0:
        for input_blob in validation_input_blob_list:
            logging.info(
                "Total underlying input_blobs found in Validation folder are %s", len(validation_input_blob_list)
            )

            input_blob.validation_successful_blob_path = input_blob.validation_successful_blob_path.replace("\\", "/")
            input_blob.underlying_blob_path = input_blob.validation_successful_blob_path.replace(
                constants.DEFAULT_VALIDATION_SUCCESSFUL_SUBFOLDER, constants.DEFAULT_UNDERLYING_SUBFOLDER
            )
            input_blob.save()
            # moving from incoming to underlying folder
            move_blob_from_source_folder_to_destination_folder_in_azure_blob_storage(
                input_blob.validation_successful_blob_path, input_blob.underlying_blob_path, blob_service_client
            )
            input_blob.is_underlying = True
            input_blob.is_active = False
            processing_lifecycle_status = LifecycleStatus(
                status=LifecycleStatusTypes.UNDERLYING,
                message="File is been underlyed by more than 6 hrs.",
                updated_date_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            )
            input_blob.lifecycle_status_list.append(processing_lifecycle_status)
            input_blob.save()


def get_list_of_input_blob_from_mongodb_in_incoming() -> List[InputBlob]:
    hours_ago = datetime.now() - timedelta(hours=6)
    input_blob_list: List[InputBlob] = InputBlob.objects(
        is_uploaded=True,
        is_processed_for_validation=False,
        is_validation_successful=False,
        is_underlying=False,
        is_processing_for_data=False,
        is_processed_for_data=False,
        is_processed_success=False,
        is_processed_failed=False,
        date_last_modified__lt=hours_ago,
    )
    if not input_blob_list:
        logging.info("No underlying_blobs found in Incoming folder")

    return input_blob_list


def get_list_of_input_blob_from_mongodb_in_validation_successful() -> List[InputBlob]:
    hours_ago = datetime.now() - timedelta(hours=6)
    input_blob_list: List[InputBlob] = InputBlob.objects(
        is_uploaded=True,
        is_processed_for_validation=True,
        is_validation_successful=True,
        is_underlying=False,
        is_processing_for_data=False,
        is_processed_for_data=False,
        is_processed_success=False,
        is_processed_failed=False,
        date_last_modified__lt=hours_ago,
    )
    if not input_blob_list:
        logging.info("No underlying_blobs found in Validation-Successful folder. ")

    return input_blob_list


def move_blob_from_source_folder_to_destination_folder_in_azure_blob_storage(
    source_blob_path: str, destination_blob_path: str, blob_service_client: BlobServiceClient
):
    """
    Moves a blob from the source folder to the destination folder in the Azure Blob Storage.


    Args:
        source_blob_path (str): Path of the blob in the source folder.
        destination_blob_path (str): Path of the blob in the destination folder.

    Returns:
        None
    """
    source_blob_client = blob_service_client.get_blob_client(
        container=constants.DEFAULT_BLOB_CONTAINER, blob=source_blob_path
    )
    destination_blob_client = blob_service_client.get_blob_client(
        container=constants.DEFAULT_BLOB_CONTAINER, blob=destination_blob_path
    )
    destination_blob_client.start_copy_from_url(source_blob_client.url)
    source_blob_client.delete_blob()
    logging.info("Blob has been moved Successfully.")
