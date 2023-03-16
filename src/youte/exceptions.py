class InvalidFileName(Exception):
    pass
    # def __str__(self):
    #     return "Incorrect file extension or file does not exist."


class InvalidRequest(Exception):
    pass


class InvalidRequestParameter(Exception):
    pass
    # def __str__(self):
    #     return "Paramater fields are invalid for this request."


class StopCollector(Exception):
    pass


class ValueAlreadyExists(Exception):
    pass


class APIError(Exception):
    pass
