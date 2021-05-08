class ExtractionError(Exception):
    """Errors while extracting the"""


class MultipleAttachments(ExtractionError):
    """Multiple Attachments for the same type"""
