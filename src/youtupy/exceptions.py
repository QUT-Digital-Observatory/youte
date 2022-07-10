class InvalidFileName(Exception):
    pass
    # def __str__(self):
    #     return "Incorrect file extension or file does not exist."


class InvalidRequestParameter(Exception):
    pass
    # def __str__(self):
    #     return "Paramater fields are invalid for this request."


class StopCollector(Exception):
    pass
