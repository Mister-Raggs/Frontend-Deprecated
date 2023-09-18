from apps.common import utils, constants
from azure.storage.blob import ContainerClient
import logging


def create_company_folder_structure(pk: str):
    container_client = utils.get_azure_storage_blob_container_client(constants.DEFAULT_BLOB_CONTAINER)
    # Create the container
    if not container_client.exists():
        logging.error(
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
        constants.DEFAULT_PREVIEW_SUBFOLDER,
        constants.DEFAULT_UNDERLYING_SUBFOLDER,
    ]
    for subfolder in subfolders_list:
        create_folder(f"{constants.COMPANY_ROOT_FOLDER_PREFIX}{pk}", subfolder, container_client)


# creating dummy file inside every company's sub-folder
def create_folder(company_folder: str, subfolder: str, container_client: ContainerClient):
    blob_client = container_client.get_blob_client(f"{company_folder}{subfolder}dummy")
    blob_client.upload_blob(b"")
