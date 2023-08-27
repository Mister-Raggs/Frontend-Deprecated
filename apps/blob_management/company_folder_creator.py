from apps.common import utils, constants
import logging


def create_company_folder_structure(pk: str):
    container_list = [container.name for container in utils.blob_service_client().list_containers()]
    container_client = utils.container_client()
    # Create the container
    if not constants.DEFAULT_BLOB_CONTAINER in container_list:
        logging.info(
            "%s container doesnot exist, creating container %s",
            constants.DEFAULT_BLOB_CONTAINER,
            constants.DEFAULT_BLOB_CONTAINER,
        )
        container_client.create_container(constants.DEFAULT_BLOB_CONTAINER)

    # Creating Folder Structure
    subfolders_list = [
        constants.DEFAULT_INCOMING_SUBFOLDER,
        constants.DEFAULT_VALIDATION_SUCCESSFUL_SUBFOLDER,
        constants.DEFAULT_VALIDATION_FAILED_SUBFOLDER,
        constants.DEFAULT_INPROGRESS_SUBFOLDER,
        constants.DEFAULT_SUCCESSFUL_SUBFOLDER,
        constants.DEFAULT_FAILED_SUBFOLDER,
    ]
    for subfolder in subfolders_list:
        create_folder(f"{constants.COMPANY_ROOT_FOLDER_PREFIX}{pk}", subfolder, container_client)


def create_folder(company_folder: str, subfolder: str, container_client):
    blob_client = container_client.get_blob_client(f"{company_folder}{subfolder}dummy")
    blob_client.upload_blob(b"")
