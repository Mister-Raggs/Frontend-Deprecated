"""
    Common constants.
"""

DEFAULT_LOG_FILE_PATH = "./logs/citadel-webapp.log"
DEFAULT_CONFIG_FOLDER_PATH = "./config-files/"
DEFAULT_LOCAL_FILE_UPLOAD_STORAGE_FOLDER = "../../local-blob-storage"
COMPANY_ROOT_FOLDER_PREFIX = "Company-"
VALIDATION_SUCCESSFUL_SUBFOLDER = "/Validation-Successful"
MONGODB_CONN_ALIAS = "citadel_frontend_app"
DEFAULT_BLOB_CONTAINER = "aarkglobal"
INCOMING_FILES_FOLDER = "Incoming-Files"

# session value keys
SESSION_USER_ROW_ID_KEY = "user_row_id"
SESSION_FIRST_NAME_KEY = "user_first_name"
SESSION_USER_MIDDLE_NAME_KEY = "user_middle_name"
SESSION_USER_LAST_NAME_KEY = "user_last_name"
SESSION_USER_EMAIL_KEY = "user_email"
SESSION_USER_ROLE_KEY = "user_role"
SESSION_USER_COMPANY_ROW_ID = "user_company_row_id"

# document upload
# Size in bytes
# max allowed is 30 MB
MAX_FILE_SIZE_ALLOWED_BYTES = 31457280
# chunk size is 300 KB
CHUNK_SIZE_BYTES = 307200
MAX_PARALLEL_FILE_UPLOADS_ALLOWED = 21
MAX_ALLOWED_FILE_UPLOADS_ON_ONE_PAGE = 150

# Default_folders_name
DEFAULT_INCOMING_SUBFOLDER = "/Incoming-Files/"
DEFAULT_VALIDATION_SUCCESSFUL_SUBFOLDER = "/Validation-Successful/"
DEFAULT_VALIDATION_FAILED_SUBFOLDER = "/Validation-Failed/"
DEFAULT_INPROGRESS_SUBFOLDER = "/Inprogress/"
DEFAULT_SUCCESSFUL_SUBFOLDER = "/Successful/"
DEFAULT_FAILED_SUBFOLDER = "/Failed/"
DEFAULT_PREVIEW_SUBFOLDER = "/Preview/"
DEFAULT_UNPROCESSED_SUBFOLDER= "/Unprocessed/"