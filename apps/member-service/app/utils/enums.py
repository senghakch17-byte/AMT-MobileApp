from enum import Enum


class DocumentType(str, Enum):
    ID_DOCUMENT = "id_document"
    CERTIFICATE = "certificate"
    TRANSCRIPT = "transcript"
    APPLICATION = "application"
    RECEIPT = "receipt"
    OTHER = "other"
