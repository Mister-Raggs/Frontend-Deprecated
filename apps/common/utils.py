import hashlib
import logging
import os
import magic

from apps.common import config_reader
from apps.common.custom_exceptions import MissingDocumentTypeException, MissingConfigException
from azure.storage.blob import BlobServiceClient, ContainerClient


# dicts for forms
user_salutations_dict = {
    "Mr.": "Mr.",
    "Miss.": "Miss.",
    "Mrs.": "Mrs.",
    "Dr.": "Dr.",
}

user_type_dict = {
    "-1": "Select User Type",
    "AARK_GLOBAL": "AARK_GLOBAL",
    "CLIENT": "CLIENT",
}

user_role_dict = {
    "-1": "Select User Role",
    "ADMIN": "ADMIN",  # AARK global admin user
    "NORMAL": "NORMAL",  # AARK global normal user
    "CLIENT_ADMIN": "CLIENT_ADMIN",  # Client admin user
    "CLIENT_NORMAL": "CLIENT_NORMAL",  # Client normal user
}

countries_dict = {
    "-1": "Select a Country",
    "US": "United States",
    "CA": "Canada",
}

us_states_dict = {
    "AK": "Alaska",
    "AL": "Alabama",
    "AR": "Arkansas",
    "AS": "American Samoa",
    "AZ": "Arizona",
    "CA": "California",
    "CO": "Colorado",
    "CT": "Connecticut",
    "DC": "District of Columbia",
    "DE": "Delaware",
    "FL": "Florida",
    "FM": "Federated States of Micronesia",
    "GA": "Georgia",
    "GU": "Guam",
    "HI": "Hawaii",
    "IA": "Iowa",
    "ID": "Idaho",
    "IL": "Illinois",
    "IN": "Indiana",
    "KS": "Kansas",
    "KY": "Kentucky",
    "LA": "Louisiana",
    "MA": "Massachusetts",
    "MD": "Maryland",
    "ME": "Maine",
    "MH": "Marshall Islands",
    "MI": "Michigan",
    "MN": "Minnesota",
    "MO": "Missouri",
    "MP": "Northern Mariana Islands",
    "MS": "Mississippi",
    "MT": "Montana",
    "NC": "North Carolina",
    "ND": "North Dakota",
    "NE": "Nebraska",
    "NH": "New Hampshire",
    "NJ": "New Jersey",
    "NM": "New Mexico",
    "NV": "Nevada",
    "NY": "New York",
    "OH": "Ohio",
    "OK": "Oklahoma",
    "OR": "Oregon",
    "PA": "Pennsylvania",
    "PR": "Puerto Rico",
    "PW": "Palau",
    "RI": "Rhode Island",
    "SC": "South Carolina",
    "SD": "South Dakota",
    "TN": "Tennessee",
    "TX": "Texas",
    "UT": "Utah",
    "VA": "Virginia",
    "VI": "Virgin Islands",
    "VT": "Vermont",
    "WA": "Washington",
    "WI": "Wisconsin",
    "WV": "West Virginia",
    "WY": "Wyoming",
}

ca_states_dict = {
    "AB": "Alberta",
    "BC": "British Columbia",
    "MB": "Manitoba",
    "NB": "New Brunswick",
    "NL": "Newfoundland",
    "NS": "Nova Scotia",
    "NT": "Northwest Territories",
    "NU": "Nunavut",
    "ON": "Ontario",
    "PE": "Prince Edward Island",
    "QC": "Quebec",
    "SK": "Saskatchewan",
    "YT": "Yukon",
}


def get_azure_storage_connection_string():
    """
    Removes " " from starting and end of the string.

    Return:
        returns connection string
    """
    if is_env_local() == True:
        if not config_reader.config_data.has_option("Main", "azure-storage-account-connection-str"):
            raise MissingConfigException("Main.azure-storage-account-connection-str is missing in config.")

        connection_string = config_reader.config_data.get("Main", "azure-storage-account-connection-str")

        if not string_is_not_empty(connection_string):
            raise MissingConfigException("Main.azure-storage-account-connection-str is present but has empty value.")

    else:
        if not config_reader.config_data.has_option("Main", "azure-storage-account-connection-str"):
            raise MissingConfigException("Main.azure-storage-account-connection-str is missing in config.")

        connection_string = config_reader.config_data.get("Main", "azure-storage-account-connection-str")

        if not string_is_not_empty(connection_string):
            raise MissingConfigException("Main.azure-storage-account-connection-str is present but has empty value.")

    if connection_string.startswith(("'", '"')) and connection_string.endswith(("'", '"')):
        connection_string = connection_string.strip("'\"")

    return connection_string


def get_mongodb_connection_string():
    """
    Removes " " from starting and end of the string.

    Return:
        returns connection string
    """

    if not config_reader.config_data.has_option("Main", "mongodb-connection-string"):
        raise MissingConfigException("Main.mongodb-connection-string.")

    connection_string = config_reader.config_data.get("Main", "mongodb-connection-string")

    if not string_is_not_empty(connection_string):
        raise MissingConfigException("Main.mongodb-connection-string is present but has empty value.")

    if connection_string.startswith(("'", '"')) and connection_string.endswith(("'", '"')):
        connection_string = connection_string.strip("'\"")

    return connection_string


def get_azure_storage_blob_service_client():
    """
    blob_service_client calls BobServiceClient

    Returns:
        BobServiceClient
    """
    return BlobServiceClient.from_connection_string(get_azure_storage_connection_string())


def get_azure_storage_blob_container_client(blob_container_name: str) -> ContainerClient:
    """
    container_client calls ContainerClient

    Returns:
        ContainerClient
    """
    blob_service_client = BlobServiceClient.from_connection_string(get_azure_storage_connection_string())
    return blob_service_client.get_container_client(blob_container_name)


def string_is_not_empty(input_str):
    return (input_str is not None) and len(input_str) > 0


def is_env_local():
    if config_reader.config_data.has_option("Main", "env"):
        env = config_reader.config_data.get("Main", "env")
    else:
        env = "local"

    return env.lower() == "local".lower()


# Helper - Extract current page name from request
def get_segment(request):
    try:
        segment = request.path.split("/")[-1]
        if segment == "":
            segment = "index"
        return segment
    except:
        return None


def get_md5_hash_for_file(file) -> str:
    md5 = hashlib.md5()
    with open(file, "rb") as f:
        for chunk in iter(lambda: f.read(128 * md5.block_size), b""):
            md5.update(chunk)
    return md5.hexdigest()


def get_file_mime_type(filepath) -> str:
    mime = magic.Magic(mime=True)
    return mime.from_file(filepath)


def get_document_type_from_file_name(file_path):
    """
    get_document_type_from_file_name Takes a filename or absolute path and extracts the
    document type form the last part of the base filename.

    e.g file_path = "/Users/xyz/Citadel-IDP-App/local-blob-storage/test-company/VALIDATION-SUCCESSFUL/1001-receipt.jpg" OR

    file_path = "../VALIDATION-SUCCESSFUL/1001-receipt.jpg" OR

    file_path = "1001-receipt.jpg"

    Should extract "receipt" as the result. Using this value as key in config, finds the
    corresponding form recognizer model for this file.

    Args:
        file_path (str): the filename or path to extract the info from.

    Raises:
        MissingDocumentTypeException: Raised if the document type cannot be inferred from the provided file_path
        or there is no form recognizer mapping in config for the inferred document type.

    Returns:
        tuple(str): the first element is the inferred document type and second element is the mapped form recognizer model.
    """

    full_file_name = os.path.basename(file_path)
    name_part = os.path.splitext(full_file_name)[0]
    index = name_part.rfind("-")
    if index == -1:
        # there was no - in the filename part. could be missing there.
        msg = f"File name path {file_path} has no hyphen (-) in it. Was expecting one."
        logging.warning(msg)
        raise MissingDocumentTypeException(msg)

    document_type = name_part[(index + 1) :]
    found = False
    if config_reader.config_data.has_section("Form-Recognizer-Document-Types"):
        for key, value in config_reader.config_data.items("Form-Recognizer-Document-Types"):
            if str(document_type).lower() == str(key).lower():
                return document_type, value

    if not found:
        msg = f"Could not find form recognizer model for document type {document_type} inferred form file name path {file_path}."
        logging.error(msg)
        raise MissingDocumentTypeException(msg)
