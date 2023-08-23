"""
All data objects declared here.
"""

from apps.common import config_reader, utils
from apps.common.custom_exceptions import CitadelIDPWebException
from apps.common import config_reader


class Metadata(object):
    """
    Metadata, represents metadata attributes for the blob.

    """

    status: str = None
    name: str = None
    url: str = None
    blob_type: str = None
    container: str = None
    last_modified: str = None
    created: str = None
    content_md5: str = None
    content_length: int = None
    content_type: str = None
    uploader_name: str = "User_who_uploaded"  # From Azure side
    user_ip: str = "IP of user"  # From Azure side

    def __repr__(self):
        return (
            "\n"
            + f"Status='{self.status}'"
            + f"\nblob_path='{self.name}'"
            + f"\nblob_url='{self.url}'"
            + f"\nblob_type='{self.blob_type}'"
            + f"\ncontainer_name='{self.container}'"
            + f"\nlast_modified='{self.last_modified}'"
            + f"\ncreatedOn='{self.created}'"
            + f"\ncontentMD5='{self.content_md5}'"
            + f"\ncontent_length_bytes='{self.content_length}'"
            + f"\ncontent_type='{self.content_type}'"
        )


class InputBlob(object):
    """
    InputBlob represents the input blob that needs to be analyzed.
    stores the information of movement of file from incomming to validation succesfull

    Raises :py:class:`CitadelIDPWebException` if invalid incoming_document_url
    is provided to constructor

    """

    incoming_blob_path: str = None
    failed_blob_path: str = None
    successful_blob_path: str = None
    blob_type: str = None
    blob_recognizer_model_id: str = None
    # is_processed mean analysis was completed.
    is_processed: bool = False
    # is_successful mean analysis was completed AND processing was successful
    is_successful: bool = False
    # is_successful mean analysis was completed AND processing failed
    is_failed: bool = False
    result_json_data: str = None
    meta: str = None

    # --------------------------------------------------------------------------------

    def __init__(
        self,
        blob_type,
        blob_recognizer_model_id,
        validation_successful_blob_path=None,
        form_recognizer_endpoint=None,
    ):
        self.document_type = blob_type
        self.document_recognizer_model_id = blob_recognizer_model_id
        if utils.string_is_not_empty(validation_successful_blob_path):
            # validation_successful_blob_path needs to be present
            self.validation_successful_blob_path = validation_successful_blob_path
        else:
            # raise exception
            raise CitadelIDPWebException(
                "To create an InputBlob validation_successful_blob_path is required, but none was provided."
            )

        # if no custom form_recognizer_endpoint provided, use the main one in config.
        if form_recognizer_endpoint is None:
            self.form_recognizer_endpoint = config_reader.config_data.get("Main", "form-recognizer-endpoint")
        else:
            self.form_recognizer_endpoint = form_recognizer_endpoint

    def __repr__(self):
        return (
            "\nInputBlob("
            + f"\nincoming_blob_path='{self.incoming_blob_path}'"
            + f"\nblob_type='{self.blob_type}'"
            + f"\nblob_recognizer_model_id='{self.blob_recognizer_model_id}'"
            + f"\nform_recognizer_endpoint='{self.form_recognizer_endpoint}'"
            + f"\nis_processed='{self.is_processed}'"
            + f"\nis_successful='{self.is_successful}'"
            + f"\nis_failed='{self.is_failed}'"
            + f"\nresult_json_data='{self.result_json_data}'"
            + ")"
            + f"\n\nMetaData: {self.meta}"
        )
