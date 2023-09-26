import base64
import binascii
from http import HTTPStatus
import logging
import  time
import os
import fitz
from PIL import Image
from pathlib import Path
from flask import make_response, session, jsonify,send_file
from flask.wrappers import Request, Response
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
from mongoengine.queryset.visitor import Q
from azure.storage.blob import BlobClient, ContentSettings, BlobServiceClient
from azure.core.exceptions import ServiceRequestError

from apps.common import config_reader, constants, utils
from apps.common.custom_exceptions import (
    DocumentManagementException,
    DocumentNotFoundException,
    CitadelIDPWebException,
    DocumentNotFoundException,
    MissingBlobException,
)
from apps.models.input_blob_model import InputBlob, LifecycleStatus, LifecycleStatusTypes, MetaData
from apps.models.user_model import user_loader

def get_latest_blob_residing_path_in_azure(document:InputBlob):
        # checking if blob is moving 
        if document.lifecycle_status_list[-1].status==LifecycleStatusTypes.INITIAL_VALIDATING or document.lifecycle_status_list[-1].status==LifecycleStatusTypes.PROCESSING:
            #returned None cause blob might be moving
             return 
        #if lying in Incoming Folder
        elif document.lifecycle_status_list[-1].status==LifecycleStatusTypes.UPLOADED and not document.is_processed_for_validation:
            if document.incoming_blob_path:
                path=document.incoming_blob_path
                return path
        #if lying in Validation Successful folder 
        elif document.lifecycle_status_list[-1].status==LifecycleStatusTypes.INITIAL_VALIDATED and not document.is_processing_for_data:
            if document.validation_successful_blob_path:
                path=document.validation_successful_blob_path
                return path
        #if lying in in progress folder
        elif document.lifecycle_status_list[-1].status==LifecycleStatusTypes.PROCESSED and not(document.is_processed_success) and not(document.is_processed_failed):
                # this is because some problem encountered in moving blob from inprogress to failed or succesful(meaning if blob strucked in inprogress folder)
                path=document.in_progress_blob_path
                return path
        #if lying in succesful folder
        elif document.lifecycle_status_list[-1].status==LifecycleStatusTypes.SUCCESS:
            if document.success_blob_path:
                path=document.success_blob_path
                return path
        #if lying in failed folder
        elif document.lifecycle_status_list[-1].status==LifecycleStatusTypes.FAILED:
                path=document.failed_blob_path
                return path
        #if lying in underlying folder
        elif document.lifecycle_status_list[-1].status==LifecycleStatusTypes.UNDERLYING:
            if document.underlying_blob_path:
                path=document.underlying_blob_path
                return path
                 
# without utilizing local storage 
def handle_document_download(document_id):
    start_time=time.time()
    span_time_in_sec=2
    while True:
        document:InputBlob = InputBlob.objects(pk=document_id).first()
        if not document:
            msg=f"document not found for document id:{document_id}"
            raise DocumentNotFoundException(msg)
        blob_path=get_latest_blob_residing_path_in_azure(document)
        if blob_path:
            blob_client = utils.get_azure_storage_blob_service_client().get_blob_client(
            container=constants.DEFAULT_BLOB_CONTAINER, blob=blob_path
            )
            if blob_client.exists():
                try:
                    download_stream = blob_client.download_blob()
                    content_type=document.metadata.content_type
                    return Response(download_stream.readall(), mimetype=content_type)
                except Exception as e:
                    logging.exception("Exception : %s ,on user clicking download button,blob is moving ",e)
        if time.time()>start_time+span_time_in_sec:
            #logically there are  only two possiblities: 
            # 1) blob does not found in  azure storage and its instance is in DB 
            # 2) or if searching time of code for blob in azure storage takes more than the span time , though blob might be existing in storage.
            # logging.error("blob  not found in azure storage but it's instance is in DB  with document_id: %s",document_id)
            msg=f"blob  not found in azure storage but it's instance is in DB  with document_id: {document_id}"
            raise MissingBlobException(msg)
            

def __create_preview_for_image_file(local_file_save_path, filename):
    # Adding suffix 'preview-' to the file name
    local_file_preview_save_path = local_file_save_path.replace(filename, "preview-{}".format(filename))
    preview_size = (400, 400)
    img = Image.open(local_file_save_path)
    img.thumbnail(preview_size)
    img.save(local_file_preview_save_path)
    logging.info("Preview %s is succesfully stored in local file storage", local_file_preview_save_path)
    return local_file_preview_save_path


def __create_preview_for_pdf_file(local_file_save_path, filename):
    # Adding suffix 'preview-' to the file name
    local_file_preview_save_path = local_file_save_path.replace(
        filename, "preview-{}".format(filename.replace("pdf", "png"))
    )
    preview_size = (400, 400)
    doc = fitz.open(local_file_save_path)
    rect = doc[0].rect
    
    if len(doc) == 1:
        # If there is only one page, create a new PDF with the same width and height as the original page
        new_page_rect = fitz.Rect(0, 0, rect.width, rect.height)
        pdf_writer = fitz.open()
        new_page = pdf_writer.new_page(width=new_page_rect.width, height=new_page_rect.height)
        # Insert the first page into the new page
        new_page.show_pdf_page(fitz.Rect(0, 0, rect.width, rect.height), doc, 0)

    elif len(doc) > 1:
        # If there are multiple pages, create a new PDF with double the width to accommodate both pages
        new_page_rect = fitz.Rect(0, 0, rect.width * 2, rect.height)
        # Creating a new PDF page with the calculated dimensions
        pdf_writer = fitz.open()
        new_page = pdf_writer.new_page(width=new_page_rect.width, height=new_page_rect.height)
        # Inserting the first page into the "new_page"
        new_page.show_pdf_page(fitz.Rect(0, 0, rect.width, rect.height), doc, 0)
        # Inserting the second page into the "new_page"
        new_page.show_pdf_page(fitz.Rect(rect.width, 0, rect.width * 2, rect.height), doc, 1)

    pix = new_page.get_pixmap()
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    img.thumbnail(preview_size)
    img.save(local_file_preview_save_path)
    logging.info("Preview %s is succesfully stored in local file storage", local_file_preview_save_path)

    return local_file_preview_save_path



def __upload_preview_file_to_azure_storage(
    preivew_blob_path, local_file_preview_save_path, blob_service_client: BlobServiceClient
):
    try:
        blob_client = blob_service_client.get_blob_client(
            container=constants.DEFAULT_BLOB_CONTAINER, blob=preivew_blob_path
        )
        # infer file mime type and set it to upload
        file_type = utils.get_file_mime_type(local_file_preview_save_path)
        content_settings = ContentSettings(content_type=file_type)
        logging.info("File '%s' content type inferred as '%s'", local_file_preview_save_path, file_type)
        with open(file=local_file_preview_save_path, mode="rb") as data:
            blob_client.upload_blob(data=data, overwrite=False, content_settings=content_settings)

        return True
    except:
        logging.exception("Failed to save Blob resource '%s' to blob storage.", preivew_blob_path)
        # cleanup from local file storage in any case
        __cleanup_local_file_storage(local_file_preview_save_path)

        return False


def __blob_exists(blob_client, blob_path):
    try:
        blob_client.get_blob_properties()
        return True
    except Exception:
        return False


def __get_local_file_save_path(filename):
    local_save_folder = config_reader.config_data.get("Main", "app_base_dir") + "\\uploaded_file_storage\\"
    local_file_name = f"user_{session.get(constants.SESSION_USER_ROW_ID_KEY)}_{filename}"
    local_file_save_path = os.path.join(
        local_save_folder,
        local_file_name,
    )
    return local_file_save_path


def __check_if_md5_hash_match(blob_client: BlobClient, local_file_save_path: str, filename: str) -> bool:
    # get md5 of blob form azure props
    properties = blob_client.get_blob_properties()
    blob_md5 = bytearray(properties.content_settings.content_md5)
    blob_md5_hex = binascii.hexlify(blob_md5).decode("utf-8")

    # get for the local file also
    md5_hash = utils.get_md5_hash_for_file(local_file_save_path)
    return md5_hash == blob_md5_hex


def __get_form_recognizer_model_type(filename):
    try:
        filename_without_ext = os.path.splitext(filename)[0]
        form_recognizer_model_type = filename_without_ext.split("-")[1]
        return form_recognizer_model_type
    except:
        raise DocumentManagementException(f"Failed to infer form recognizer model type from file name {filename}")


def __cleanup_local_file_storage(local_file_save_path):
    # Step 8 - cleanup from local file storage in any case
    file_to_rem = Path(local_file_save_path)
    file_to_rem.unlink(missing_ok=True)
    logging.info("Local file '%s' cleaned up successfully.", local_file_save_path)


def __validate_chunk_size(request: Request) -> Response:
    # Step 1 - check chunk size allowed.
    chunk_size = int(request.form["dzchunksize"])
    if chunk_size > constants.CHUNK_SIZE_BYTES:
        logging.error(
            "Received a chunk of size %s bytes which is more than the configured default chunk size of %s bytes from the incoming request.",
            chunk_size,
            constants.CHUNK_SIZE_BYTES,
        )
        return make_response(("Request data chunk size exceeds max allowed chunk size.", HTTPStatus.BAD_REQUEST))


def __validate_container_and_blob_already_exist(
    blob_service_client: BlobServiceClient,
    blob_client: BlobClient,
    blob_path,
    current_chunk,
    local_file_save_path,
) -> Response:
    container_client = blob_service_client.get_container_client(constants.DEFAULT_BLOB_CONTAINER)
    try:
        # Check container exists
        if not container_client.exists():
            logging.error("Root Blog storage container %s  doesn't exist.", constants.DEFAULT_BLOB_CONTAINER)
            return make_response(
                f"Root Blog storage container {constants.DEFAULT_BLOB_CONTAINER} doesn't exist.", HTTPStatus.BAD_REQUEST
            )

        # Check blob exists
        if (current_chunk == 0) and __blob_exists(blob_client, blob_path):
            logging.error("File Blob resource '%s' already exists", blob_path)
            return make_response("File Blob resource already exists.", HTTPStatus.BAD_REQUEST)

    except ServiceRequestError as e:
        logging.exception("Azure blob service error.")
        # cleanup from local file storage in any case
        __cleanup_local_file_storage(local_file_save_path)
        return make_response(f"Document blob upload error. Please try again later.", HTTPStatus.INTERNAL_SERVER_ERROR)


def __validate_file_exists_on_local_storage(local_file_save_path, current_chunk) -> Response:
    if os.path.exists(local_file_save_path) and (current_chunk == 0):
        logging.error("File already in local storage '%s' already exists", local_file_save_path)
        return make_response("File already uploaded.", 400)


def __save_file_chunk_to_local_storage(local_file_save_path, request: Request, file_data: FileStorage) -> Response:
    try:
        with open(local_file_save_path, "ab") as f:
            f.seek(int(request.form["dzchunkbyteoffset"]))
            f.write(file_data.stream.read())
    except OSError:
        logging.exception("Could not write to file '%s'", local_file_save_path)
        return make_response("Failed to write the file to disk", 500)


def __upload_blob_to_azure_storage(
    blob_client: BlobClient,
    blob_path,
    local_file_save_path,
) -> Response:
    try:
        # infer file mime type and set it to upload
        file_type = utils.get_file_mime_type(local_file_save_path)
        content_settings = ContentSettings(content_type=file_type)
        logging.info("File '%s' content type inferred as '%s'", local_file_save_path, file_type)

        with open(file=local_file_save_path, mode="rb") as data:
            blob_client.upload_blob(data=data, overwrite=False, content_settings=content_settings)
    except:
        logging.exception("Failed to save Blob resource '%s' to blob storage.", blob_path)
        # cleanup from local file storage in any case
        __cleanup_local_file_storage(local_file_save_path)
        return make_response("Failed to save file to blob storage.", HTTPStatus.BAD_REQUEST)


def __save_input_blob_to_db_and_cleanup_local_storage(
    blob_client: BlobClient,
    local_file_save_path,
    form_recognizer_model_type,
    blob_path,
) -> Response:
    properties = blob_client.get_blob_properties()
    uploader_user = user_loader(session.get(constants.SESSION_USER_ROW_ID_KEY))
    blob_md5_str = base64.b64encode(properties.content_settings.content_md5).decode("utf-8")

    metadata = MetaData(
        blob_type=properties.blob_type,
        form_recognizer_model_type=form_recognizer_model_type,
        blob_azure_last_modified=properties.last_modified,
        blob_azure_created_on=properties.creation_time,
        content_md5=blob_md5_str,
        content_length_bytes=properties.size,
        content_type=properties.content_settings.content_type,
        blob_access_tier=properties.blob_tier,
        blob_lease_state=properties.lease.state,
        blob_lease_status=properties.lease.status,
        blob_azure_encrypted=properties.server_encrypted,
        # TODO: change this when we implement our encryption for blob contents
        blob_citadel_encrypted=False,
    )

    lifecycle_status = LifecycleStatus(
        status=LifecycleStatusTypes.UPLOADED,
        message="File blob uploaded successfully",
        updated_date_time=properties.last_modified,
    )

    input_blob = InputBlob(
        blob_name=os.path.basename(blob_client.blob_name),
        blob_container_name=blob_client.container_name,
        incoming_blob_path=blob_client.blob_name,
        incoming_blob_url=blob_client.primary_endpoint,
        is_processed_for_validation=False,
        is_validation_successful=False,
        uploader_user=uploader_user,
        uploader_company=uploader_user.company,
        is_active=True,
        is_deleted=False,
        metadata=metadata,
    )
    input_blob.lifecycle_status_list.append(lifecycle_status)

    try:
        input_blob.save()
    except:
        logging.exception("Saving to DB failed. Blob path '%s' will be deleted from blob storage.", blob_path)
        blob_client.delete_blob(delete_snapshots="include")
        return make_response("Failed to save the file details to DB.", HTTPStatus.INTERNAL_SERVER_ERROR)
    finally:
        # ------------------------------------------------------
        # Step 8 - cleanup from local file storage in any case
        __cleanup_local_file_storage(local_file_save_path)


def handle_document_upload(request: Request) -> Response:
    file_data = request.files["citadel_file_upload_dropper"]
    filename = secure_filename(file_data.filename)

    if file_data and filename:
        form_recognizer_model_type = __get_form_recognizer_model_type(filename)
        user_company_row_id = session.get(constants.SESSION_USER_COMPANY_ROW_ID)
        current_chunk = int(request.form["dzchunkindex"])
        local_file_save_path = __get_local_file_save_path(filename)

        # ------------------------------------------------------
        # Step 1 - check chunk size allowed.
        response = __validate_chunk_size(request)
        if response:
            return response

        # ------------------------------------------------------
        # Step 2 - check if Root Blog storage container exists and document already exists on azure blob storage.
        blob_folder_name = f"{constants.COMPANY_ROOT_FOLDER_PREFIX}{user_company_row_id}"
        blob_service_client = utils.get_azure_storage_blob_service_client()
        blob_path = os.path.join(blob_folder_name, constants.INCOMING_FILES_FOLDER, filename)
        blob_client = blob_service_client.get_blob_client(container=constants.DEFAULT_BLOB_CONTAINER, blob=blob_path)

        response = __validate_container_and_blob_already_exist(
            blob_service_client, blob_client, blob_path, current_chunk, local_file_save_path
        )
        if response:
            return response

        # ------------------------------------------------------
        # Step 3 - check if the document exists on local storage i.e. is it uploaded twice at the same time?
        response = __validate_file_exists_on_local_storage(local_file_save_path, current_chunk)
        if response:
            return response

        # ------------------------------------------------------
        # Step 4 - start saving the file chunks to local storage
        response = __save_file_chunk_to_local_storage(local_file_save_path, request, file_data)
        if response:
            return response

        # process last chunk
        total_chunks = int(request.form["dztotalchunkcount"])
        if current_chunk + 1 == total_chunks:
            # This was the last chunk, the file should be complete and the size we expect
            if os.path.getsize(local_file_save_path) != int(request.form["dztotalfilesize"]):
                logging.error(
                    "File '%s' was saved, but has a size mismatch. Was '%s' but we expected '%s'",
                    local_file_save_path,
                    os.path.getsize(local_file_save_path),
                    request.form["dztotalfilesize"],
                )
                return make_response(("Uploaded file size mismatch.", 500))
            else:
                logging.info("File '%s' has been saved successfully to local storage.", local_file_save_path)

                # ------------------------------------------------------
                # Step 5 - upload the file to azure blob storage
                response = __upload_blob_to_azure_storage(blob_client, blob_path, local_file_save_path)
                if response:
                    return response

                # ------------------------------------------------------
                #step 6 Generating preview for file
                preview_generated :bool = False
                try:
                    if "pdf" in filename:
                        preivew_file_local_save_path = __create_preview_for_pdf_file(local_file_save_path, filename)
                        preview_blob_path = os.path.join(
                            blob_folder_name,
                            constants.PREVIEW_FILES_FOLDER,
                            "preview-{}".format(filename.replace("pdf", "png")),
                        )
                        preview_generated = __upload_preview_file_to_azure_storage(
                            preview_blob_path, preivew_file_local_save_path, blob_service_client
                        )

                    elif "jpg" in filename or "jpeg" in filename or "png" in filename:
                        preivew_file_local_save_path = __create_preview_for_image_file(local_file_save_path, filename)
                        preview_blob_path = os.path.join(
                            blob_folder_name, constants.PREVIEW_FILES_FOLDER, "preview-{}".format(filename)
                        )
                        preview_generated = __upload_preview_file_to_azure_storage(
                            preview_blob_path, preivew_file_local_save_path, blob_service_client
                        )

                except Exception as err:
                    logging.error("An error occured while generating preview : %s ",err)

                # ------------------------------------------------------
                # Step 7 - check the MD5 has of the uploaded blob. Calculate MD5 of local file and match that to what we get in blob properties.
                if __check_if_md5_hash_match(blob_client, local_file_save_path, filename):
                    logging.info("File '%s' successfully uploaded to azure blob storage.", blob_path)

                    # ------------------------------------------------------
                    # Step 8 - save the blob info to mongodb
                    response = __save_input_blob_to_db_and_cleanup_local_storage(
                        blob_client, local_file_save_path, form_recognizer_model_type, blob_path
                    )
                    if response:
                        return response

                else:
                    logging.error(
                        "MD5 hashes dont match for local file '%s' and uploaded blob '%s'.",
                        local_file_save_path,
                        blob_path,
                    )
                    return make_response("File Blob MD5 hashes dont match.", HTTPStatus.INTERNAL_SERVER_ERROR)

                # ----------------------------------------------------------
                # step 9 - preview save_input_blob_to_db_and_cleanup_local_storage
                if preview_generated:
                    input_blob: InputBlob = InputBlob.objects(incoming_blob_path=blob_path).first()
                    input_blob.preview_blob_path = preview_blob_path
                    input_blob.save()

                    if os.path.exists(preivew_file_local_save_path):
                        __cleanup_local_file_storage(preivew_file_local_save_path)

                # ----------------------------------------------------------
        return make_response("Chunk upload successful", 200)
    else:
        msg = "Improper or incomplete request received. Either filename or the file data is missing."
        logging.error(msg)
        make_response(msg, HTTPStatus.BAD_REQUEST)


# list all documents form input blob using row id
def get_input_document_blobs_by_row_id(row_id) -> InputBlob:
    document = InputBlob().objects(id=row_id).first()
    return document


#  function for activate and de-activate documents
def handle_document_toggle_activate_delete(document_id, action):
    document: InputBlob = InputBlob.objects(pk=document_id).first()
    old_value = False
    new_value = False
    if document:
        if action.lower() == "is_active":
            old_value = document.is_active
            if old_value:
                document.is_active = False
                new_value = False
            else:
                document.is_active = True
                new_value = True
        else:
            raise CitadelIDPWebException(f"Invalid toggle action '{action}' requested.")
        document.save()
        logging.info("Successfully toggled '%s' from %s to %s", action, old_value, new_value)
    else:
        msg = f"toggle activate operation failed. No document found with id {document_id}"
        raise DocumentNotFoundException(msg)


# prepare the data for list all documents uploaded.
def prepare_document_list_data(draw, search_value, start_index, page_length):
    """
    prepare_document_list_data _summary_
    Args:
        draw (_type_): _description_
        search_value (_type_): _description_
        page_start (int): zero based page number. i.e. page 0 means its page 1
        page_length (int): number of records to fetch per page.
    """
    end_index = start_index + page_length
    document_data = None
    records_total = InputBlob.objects().count()
    records_filtered = records_total
    if utils.string_is_not_empty(search_value):
        document_data = InputBlob.objects(Q(blob_name__icontains=search_value))[start_index:end_index]
        # get the count of records also
        records_filtered = InputBlob.objects(Q(blob_name__icontains=search_value)).count()
    else:
        document_data = InputBlob.objects[start_index:end_index]
    # logging.info(document_data)
    response_data = []
    for document in document_data:
        size_in_mb = document.metadata.content_length_bytes / (1024 * 1024)
        document_type_size = f"{size_in_mb:.2f} MB, {document.metadata.content_type}"
        user_full_name = f" {document.uploader_user.first_name}"
        if utils.string_is_not_empty(document.uploader_user.middle_name):
            user_full_name += f" {document.uploader_user.middle_name}"
        user_full_name += f"{document.uploader_user.last_name}"
        last_status = document.lifecycle_status_list[-1]
        final_status = f"{last_status.status.name} , {last_status.updated_date_time}"
        response_data.append(
            {
                "DT_RowId": str(document.pk),
                "document_name": document.blob_name,
                "uploaded_by": user_full_name,
                "document_type_size": document_type_size,
                "created_date": document.date_created,
                "last_modified_date": document.date_last_modified,
                "latest_status": final_status,
                "is_active": "Yes" if (document.is_active) else "No",
            }
        )
    response = {
        "draw": draw,
        "recordsFiltered": records_filtered,
        "recordsTotal": records_total,
        "data": response_data,
    }
    # logging.info("response -> %s", response)
    return jsonify(response)


# prepare the data for list all underlying documents uploaded.
def prepare_list_underlying_data(draw, search_value, start_index, page_length):
    """
    prepare_underlying_document_list_data _summary_
    Args:
        draw (_type_): _description_
        search_value (_type_): _description_
        page_start (int): zero based page number. i.e. page 0 means its page 1
        page_length (int): number of records to fetch per page.
    """
    end_index = start_index + page_length
    document_data = None
    records_total = InputBlob.objects(is_underlying=True, is_active=False).count()
    records_filtered = records_total
    if utils.string_is_not_empty(search_value):
        document_data = InputBlob.objects(
            (Q(is_underlying=True) & Q(is_active=False) & Q(blob_name__icontains=search_value))
        )[start_index:end_index]
        # get the count of records also
        records_filtered = InputBlob.objects(
            (Q(is_underlying=True) & Q(is_active=False) & Q(blob_name__icontains=search_value))
        ).count()
    else:
        document_data = InputBlob.objects(Q(is_underlying=True) & Q(is_active=False))[start_index:end_index]
    # logging.info(document_data)
    response_data = []
    for document in document_data:
        size_in_mb = document.metadata.content_length_bytes / (1024 * 1024)
        document_type_size = f"{size_in_mb:.2f} MB, {document.metadata.content_type}"
        user_full_name = f" {document.uploader_user.first_name}"
        if utils.string_is_not_empty(document.uploader_user.middle_name):
            user_full_name += f" {document.uploader_user.middle_name}"
        user_full_name += f"{document.uploader_user.last_name}"
        last_status = document.lifecycle_status_list[-1]
        final_status = f"{last_status.status.name} , {last_status.updated_date_time}"
        response_data.append(
            {
                "DT_RowId": str(document.pk),
                "document_name": document.blob_name,
                "uploaded_by": user_full_name,
                "document_type_size": document_type_size,
                "created_date": document.date_created,
                "last_modified_date": document.date_last_modified,
                "latest_status": final_status,
                "is_active": "Yes" if (document.is_active) else "No",
            }
        )
    response = {
        "draw": draw,
        "recordsFiltered": records_filtered,
        "recordsTotal": records_total,
        "data": response_data,
    }
    # logging.info("response -> %s", response)
    return jsonify(response)


# prepare the data for list all underlying documents uploaded.
def prepare_list_underlying_data(draw, search_value, start_index, page_length):
    """
    prepare_underlying_document_list_data _summary_
    Args:
        draw (_type_): _description_
        search_value (_type_): _description_
        page_start (int): zero based page number. i.e. page 0 means its page 1
        page_length (int): number of records to fetch per page.
    """
    end_index = start_index + page_length
    document_data = None
    records_total = InputBlob.objects(is_underlying=True, is_active=False).count()
    records_filtered = records_total

    if utils.string_is_not_empty(search_value):
        document_data = InputBlob.objects(
            (Q(is_underlying=True) & Q(is_active=False) & Q(blob_name__icontains=search_value))
        )[start_index:end_index]
        # get the count of records also
        records_filtered = InputBlob.objects(
            (Q(is_underlying=True) & Q(is_active=False) & Q(blob_name__icontains=search_value))
        ).count()
    else:
        document_data = InputBlob.objects(Q(is_underlying=True) & Q(is_active=False))[start_index:end_index]
    # logging.info(document_data)
    response_data = []

    for document in document_data:
        size_in_mb = document.metadata.content_length_bytes / (1024 * 1024)
        document_type_size = f"{size_in_mb:.2f} MB, {document.metadata.content_type}"
        user_full_name = f" {document.uploader_user.first_name}"

        if utils.string_is_not_empty(document.uploader_user.middle_name):
            user_full_name += f" {document.uploader_user.middle_name}"
        user_full_name += f"{document.uploader_user.last_name}"
        last_status = document.lifecycle_status_list[-1]
        final_status = f"{last_status.status.name} , {last_status.updated_date_time}"
        response_data.append(
            {
                "DT_RowId": str(document.pk),
                "document_name": document.blob_name,
                "uploaded_by": user_full_name,
                "document_type_size": document_type_size,
                "created_date": document.date_created,
                "last_modified_date": document.date_last_modified,
                "latest_status": final_status,
                "is_active": "Yes" if (document.is_active) else "No",
            }
        )
    response = {
        "draw": draw,
        "recordsFiltered": records_filtered,
        "recordsTotal": records_total,
        "data": response_data,
    }
    # logging.info("response -> %s", response)
    return jsonify(response)


# Function for showing preview of blobs.
def handle_document_preview(document_id):
    document = InputBlob.objects(pk=document_id).first()
    blob_path = document.preview_blob_path
    if blob_path:
        try:
            blob_path = blob_path.replace("\\", "/")
            blob_service_client = utils.get_azure_storage_blob_service_client()
            blob_client = blob_service_client.get_blob_client(
                container=constants.DEFAULT_BLOB_CONTAINER, blob=blob_path
            )
            stream = blob_client.download_blob()
            return Response(stream.readall(), mimetype="image/png")
        except Exception as e:
            logging.exception(f"error occured in returning the respnse : {e} ")
    else:
        return jsonify({"status": "error", "message": "Document not found"}), 404
    