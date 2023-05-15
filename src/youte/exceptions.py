class InvalidFileName(Exception):
    pass


class InvalidRequest(Exception):
    pass


class InvalidRequestParameter(Exception):
    pass


class StopCollector(Exception):
    pass


class ValueAlreadyExists(Exception):
    pass


class APIError(Exception):
    pass


class CommentsDisabled(Exception):
    pass


class MaxQuotaReached(APIError):
    pass
