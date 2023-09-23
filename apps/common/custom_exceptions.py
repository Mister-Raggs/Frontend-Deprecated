"""
    This module contains the list of all custom exceptions for Citadel IDP
"""


class CitadelIDPWebException(Exception):
    """
    Generic Citadel IDP Web Exception to be raised for any high level processing failures.
    """


class MissingConfigException(CitadelIDPWebException):
    """
    Exception to be raised when some config is missing or empty.
    """


class MissingDocumentTypeException(CitadelIDPWebException):
    """
    Exception to be raised when document type cannot be inferred from file name.
    """

class MissingBlobException(CitadelIDPWebException):
    """
    exception to be raised when blob is missing from azure storage
    """

class DocumentManagementException(CitadelIDPWebException):
    """
    Exception in general document management.
    """


class CompanyNotFoundException(CitadelIDPWebException):
    """
    Exception to be raised when company is not found.
    """


class UserNotFoundException(CitadelIDPWebException):
    """
    Exception to be raised when user is not found.
    """


class UserSaveException(CitadelIDPWebException):
    """
    Exception to be raised when user cannot eb saved
    """


class CitadelDBException(CitadelIDPWebException):
    """
    Exception to be raised for all DB related operations.
    """


class MissingFolderException(CitadelIDPWebException):
    """
    Exception to be raised for missing folders.
    """


class DocumentNotFoundException(CitadelIDPWebException):
    """
    Exception to be raised if document is not found.
    """


class JobExecutionException(CitadelIDPWebException):
    """
    Exception to be raised when a a job fails.
    """
