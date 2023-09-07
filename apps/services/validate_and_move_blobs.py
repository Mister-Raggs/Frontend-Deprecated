from apps.common import utils, constants
import logging
from apps.models.input_blob_model import InputBlob, LifecycleStatus, LifecycleStatusTypes, MetaData
from typing import List
from azure.storage.blob import BlobServiceClient


def check_validate_and_move_blob():
    """
    Checks and processes the Db and move files in Azure Blob Storage.

    """
    blob_service_client = utils.get_azure_storage_blob_service_client()
    logging.info("getting list of input_blobs from Mongodb.")
    input_blob_list = get_list_of_input_blob_from_mongodb()

    # updating the picked validation to True as blob will not be picked by other instances if it's true.
    for input_blob in input_blob_list:
        input_blob.is_picked_for_validation = True
        # Saving input_blob to Mongodb.
        save_input_blob(input_blob)

    for input_blob in input_blob_list:
        if not input_blob.incoming_blob_path.startswith(constants.COMPANY_ROOT_FOLDER_PREFIX):
            logging.error(f"Input Blob '{input_blob.incoming_blob_path}'can't be Validated.")
        else:
            logging.info("Starting validating for '%s' ....", input_blob.incoming_blob_path)
            processing_lifecycle_status = LifecycleStatus(
                status=LifecycleStatusTypes.INITIAL_VALIDATING,
                message="File is getting validated",
                updated_date_time=input_blob.date_last_modified,
            )
            input_blob.lifecycle_status_list.append(processing_lifecycle_status)
            save_input_blob(input_blob)

            # Start the Validation of Input_blob
            if validate_blob(input_blob):
                input_blob.is_processed_for_validation = True
                input_blob.incoming_blob_path = input_blob.incoming_blob_path.replace("\\", "/")
                input_blob.validation_successful_blob_path = input_blob.incoming_blob_path.replace(
                    constants.DEFAULT_INCOMING_SUBFOLDER, constants.DEFAULT_VALIDATION_SUCCESSFUL_SUBFOLDER
                )
                save_input_blob(input_blob)

                move_blob_from_source_folder_to_destination_folder_in_azure_blob_storage(
                    input_blob.incoming_blob_path, input_blob.validation_successful_blob_path, blob_service_client
                )
                processing_lifecycle_status = LifecycleStatus(
                    status=LifecycleStatusTypes.INITIAL_VALIDATED,
                    message="File has been validated successful",
                    updated_date_time=input_blob.date_last_modified,
                )
                input_blob.lifecycle_status_list.append(processing_lifecycle_status)
                input_blob.is_validation_successful = True
                save_input_blob(input_blob)

            else:
                logging.info(f"{input_blob.incoming_blob_path} is not valid. Moving to validation failed folder")
                input_blob.incoming_blob_path = input_blob.incoming_blob_path.replace("\\", "/")
                input_blob.validation_successful_blob_path = input_blob.incoming_blob_path.replace(
                    constants.DEFAULT_INCOMING_SUBFOLDER, constants.DEFAULT_VALIDATION_FAILED_SUBFOLDER
                )
                input_blob.save()
                move_blob_from_source_folder_to_destination_folder_in_azure_blob_storage(
                    input_blob.incoming_blob_path, input_blob.validation_failed_blob_path, blob_service_client
                )
                processing_lifecycle_status = LifecycleStatus(
                    status=LifecycleStatusTypes.INITIAL_VALIDATED,
                    message="File failed to validate",
                    updated_date_time=input_blob.date_last_modified,
                )
                input_blob.lifecycle_status_list.append(processing_lifecycle_status)
                save_input_blob(input_blob)


def get_list_of_input_blob_from_mongodb() -> List[InputBlob]:
    initial_input_blob_list: List[InputBlob] = InputBlob.objects(
        is_picked_for_validation=False,
        is_uploaded=True,
        is_processed_for_validation=False,
        is_validation_successful=False,
        is_processing_for_data=False,
        is_processed_for_data=False,
        is_processed_success=False,
        is_processed_failed=False,
        # date_last_modified__lte=
    )

    if not initial_input_blob_list:
        logging.info("No Input_blobs found for validation")
    logging.info("Total validation input_blobs found are %s", len(initial_input_blob_list))

    return initial_input_blob_list


def validate_blob(input_blob: InputBlob) -> bool:
    if input_blob.metadata.content_length_bytes < constants.MAX_FILE_SIZE_ALLOWED_BYTES:
        if not (
            ".exe" in input_blob.incoming_blob_path
            or ".bat" in input_blob.incoming_blob_path
            or ".com" in input_blob.incoming_blob_path
            or ".cmd" in input_blob.incoming_blob_path
            or ".inf" in input_blob.incoming_blob_path
            or ".ipa" in input_blob.incoming_blob_path
            or ".osx" in input_blob.incoming_blob_path
            or ".pif" in input_blob.incoming_blob_path
            or ".run" in input_blob.incoming_blob_path
            or ".wsh" in input_blob.incoming_blob_path
        ):
            return True
    else:
        return False


def move_blob_from_source_folder_to_destination_folder_in_azure_blob_storage(
    source_blob_path: str, destination_blob_path: str, blob_service_client: BlobServiceClient
):
    """
    Moves a blob from the source folder to the destination folder in the Azure Blob Storage.



    Args:
        source_blob_path (str): Path of the blob in the source folder.
        destination_blob_path (str): Path of the blob in the destination folder.
        input_blob (InputBlob): The input_blob being moved.

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


def save_input_blob(input_blob: InputBlob):
    try:
        input_blob.save()
    except:
        logging.exception("Saving status of %s to DB failed.", input_blob.incoming_blob_path)
