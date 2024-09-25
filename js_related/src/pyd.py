
import sqlmodel
import typing

class MyClassBase(sqlmodel.SQLModel,table=True):
    id:int|None=sqlmodel.Field(primary_key=True)
    s:str
    parent:int=sqlmodel.Field(foreign_key='myclassbase.id')
    __mapper_args__={
        'polymorphic_abstract':True,
        'polymorphic_on':'s'
    }

class MyClass(MyClassBase,table=True):
    s:typing.Literal['myc1']
    i:int=sqlmodel.Field(primary_key=True)
    child:MyClassBase|None=sqlmodel.Relationship()

class MyClass2(MyClassBase,table=True):
    s:typing.Literal['myc2']
    i:int=sqlmodel.Field(primary_key=True)


myc=MyClass.model_validate_json('{"s":"myc1","i":"9","child":{"s":"myc2","i":0}}')

print(myc)