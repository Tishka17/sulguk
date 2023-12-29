class ManagerError(Exception):
    pass


class LinkedMessageNotFoundError(ManagerError):
    pass


class ChatNotFoundError(ManagerError):
    pass
