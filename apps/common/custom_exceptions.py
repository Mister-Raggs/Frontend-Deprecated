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


class DocumentManagementException(CitadelIDPWebException):
    """
    Exception to be raised when document type cannot be inferred from file name.
    """


class CompanyNotFoundException(CitadelIDPWebException):
    """
    Exception to be raised when document type cannot be inferred from file name.
    """


class UserNotFoundException(CitadelIDPWebException):
    """
    Exception to be raised when document type cannot be inferred from file name.
    """


class UserSaveException(CitadelIDPWebException):
    """
    Exception to be raised when document type cannot be inferred from file name.
    """


class CitadelDBException(CitadelIDPWebException):
    """
    Exception to be raised for all DB related operations.
    """


class ContainerMissingException(CitadelIDPWebException):
    """
    Exception to be raised if default container dosen't exists.
    """
