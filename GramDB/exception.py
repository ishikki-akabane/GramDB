class GramDBError(Exception):
    pass

class ConnectionError(GramDBError):
    pass

class NotFoundError(GramDBError):
    pass

class DuplicateTableError(GramDBError):
    pass

class ValidationError(GramDBError):
    pass
    

