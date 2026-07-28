import pydantic
from typing import Annotated, Literal, Self


def name_is_fred(value: str) -> str:
    if value != "Fred":
        raise AssertionError("Name must be 'Fred'")
    return value


class TestModel(pydantic.BaseModel):
    name: Annotated[str, pydantic.AfterValidator(name_is_fred)]
    age: int = pydantic.Field(..., ge=0, le=12)  # Age must be between 0 and 120


class TestModel2(pydantic.BaseModel):
    title: str
    description: str
    members: list[TestModel]


tm2 = TestModel2.model_validate(
    {
        "title": "Project A",
        "description": "Description of Project A",
        "members": [{"name": "Fred", "age": 3}, {"name": "Fred", "age": 2}],
    }
)
print(tm2)

try:
    failing_model = TestModel2.model_validate(
        {
            "title": "Project A",
            "description": "Description of Project A",
            "members": [
                {"age": 3},
                {"name": "Bob", "age": "twenty-five"},
            ],
        }
    )
except pydantic.ValidationError as e:
    for error in e.errors():
        print(f"Error in field '{error['loc']}': {error['type']} - {error['msg']}")
