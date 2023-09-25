class ManagerError(Exception):
    pass


class LinkedMessageNotFound(ManagerError):
    pass


class ChatNotFound(ManagerError):
    pass
