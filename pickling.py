from typing import Protocol,assert_type


class DatastoreEntry:
    field1:str
    field2:str
    field3:str

class DEP(DatastoreEntry,Protocol):
    pass

class DEP2:
    field1:str
    field2:str
    field4:str

assert_type(DEP2(),dict)




