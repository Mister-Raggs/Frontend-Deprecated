import os
import logging
import threading
import io
from flask import make_response
from flask.wrappers import Request, Response
from werkzeug.utils import secure_filename
from azure.storage.blob import BlobServiceClient, BlobType, BlobClient, ContentSettings
from concurrent.futures import ThreadPoolExecutor
from apps.common import utils, constants
from apps.common.utils import save_input_blob_to_mongodb

# Azurite Emulator configuration
azurite_connection_string = utils.get_connection_string()
logging.info(azurite_connection_string)

folder_name = "Company-A"  # The name of the folder inside the container
subfolder_name = "Incoming"  # The name of the subfolder inside the folder


# Define chunk size and max file size (in bytes)
DEFAULT_CHUNK_SIZE = 5 * 1024  # 0.5MB
MAX_FILE_SIZE = 1000 * 1024 * 1024  # 1GB


def blob_exists(blob_client, blob_path):
    try:
        blob_client.get_blob_properties()
        return True
    except Exception:
        return False


def upload_chunk(blob_client, chunk_data):
    blob_client.upload_blob(chunk_data, blob_type="AppendBlob")


def handle_seq(request: Request) -> Response:
    file_data = request.files["citadel_file_upload_dropper"]
    filename = secure_filename(file_data.filename)

    blob_service_client = BlobServiceClient.from_connection_string(azurite_connection_string)

    container_client = blob_service_client.get_container_client(constants.DEFAULT_BLOB_CONTAINER)
    if not container_client.exists():
        container_client.create_container()

    blob_path = os.path.join(folder_name, subfolder_name, filename)
    blob_client = blob_service_client.get_blob_client(container=constants.DEFAULT_BLOB_CONTAINER, blob=blob_path)

    current_chunk = int(request.form["dzchunkindex"])
    total_chunks = int(request.form["dztotalchunkcount"])

    # Adjust chunk size if provided in the request form data
    chunk_size = int(request.form.get("dzchunksize", DEFAULT_CHUNK_SIZE))

    if chunk_size > MAX_FILE_SIZE:
        return make_response(("Chunk size exceeds max file size", 400))

    if current_chunk == 0:
        if blob_exists(blob_client, blob_path):
            return make_response(("File already exists.", 400))
        blob_client.create_append_blob()

    chunk_offset = current_chunk * chunk_size
    chunk_data = file_data.stream.read(chunk_size)
    blob_client.append_block(chunk_data)

    if current_chunk == total_chunks - 1:
        blob_properties = blob_client.get_blob_properties()
        if blob_properties.size != int(request.form["dztotalfilesize"]):
            return make_response(("Size mismatch", 500))
        logging.info("File %s has been uploaded successfully.", file_data.filename)
    else:
        logging.info("Chunk %s of %s for file %s complete", current_chunk + 1, total_chunks, file_data.filename)
    save_input_blob_to_mongodb(status=subfolder_name, path=blob_path)
    return make_response(("Chunk upload successful", 200))
