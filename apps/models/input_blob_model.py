
from apps.models.base_model import BaseModel
import mongoengine as me
from enum import Enum


class ContentLengthUnit(str, Enum):
    unit="bytes"
    
    
class ContentLength(me.EmbeddedDocument):
    size=me.IntField(required=True)
    unit=me.EnumField(ContentLengthUnit,required=True,default=ContentLengthUnit.unit)
     
     
class MetaData(me.EmbeddedDocument):
    """
    Metadata, represents metadata attributes for the blob.

    """

    input_blob_status = me.StringField(required=True)
    blob_type = me.StringField(required=True)
    blob_container = me.StringField(required=True)   
    blob_last_modified = me.StringField(required=True)
    blob_created_on  = me.StringField(required=True)
    content_md5 = me.StringField(required=True)
    content_length  =me.EmbeddedDocumentField(ContentLength)
    content_type = me.StringField(required=True)
    #To do 
    # company_name,row_id,name_of_file_uploader,row_id also to be added as properties.

    def __repr__(self):
        return (
            "\n"
            + f"Status='{self.input_blob_status}'"
            + f"\nblob_type='{self.blob_type}'"
            + f"\ncontainer_name='{self.blob_container}'"
            + f"\nlast_modified='{self.blob_last_modified}'"
            + f"\ncreatedOn='{self.blob_created_on}'"
            + f"\ncontentMD5='{self.content_md5}'"
            + f"\ncontent_length_bytes='{self.content_length}'"
            + f"\ncontent_type='{self.content_type}'"
        )


class InputBlob(BaseModel):
    """
    InputBlob represents the input blob that needs to be analyzed.
    stores the information of movement of file from incomming to validation succesfull

    """
    blob_name  = me.StringField(required=True)
    incoming_blob_path= me.StringField(required=True)
    incomming_blob_url=me.URLField(max_length=200)
    failed_blob_path = me.StringField(required=False)
    failed_blob_url=me.URLField(max_length=200,required=False)
    validation_successful_blob_path = me.StringField(required=False)
    validation_successful_blob_url=me.URLField(max_length=200,required=False)
    # is_processed_for_validation mean validation check was completed.
    is_processed_for_validation  = me.BooleanField(required=True)
    # is_validation_successful mean if validation was successful or not 
    is_validation_successful  = me.BooleanField(required=True)
      
    meta_object = me.EmbeddedDocumentField(MetaData,required=True)
    # --------------------------------------------------------------------------------

    def __repr__(self):
        return (
            "\nInputBlob("
            + f"\nblob_path='{self.blob_name}'"
            + f"\nblob_url='{self.incomming_blob_url}'"
            + f"\nincoming_blob_path='{self.incoming_blob_path}'"
            +f"\nfailed_blob_path='{self.failed_blob_path}'"
            +f"\nfailed_blob_url='{self.failed_blob_url}'"
            +f"\nvalidation_successful_blob_path='{self.validation_successful_blob_path}'"
            +f"\nvalidation_successful_blob_url='{self.validation_successful_blob_url}'"
            + f"\nis_processed_for_validation='{self.is_processed_for_validation}'"
            + f"\nis_validation_successful='{self.is_validation_successful}'"
            + ")"
            + f"\n\nMetaData: {self.meta_object}"
        )
