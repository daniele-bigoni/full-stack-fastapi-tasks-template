from sqlmodel import SQLModel, Field


class SampleBaseRandomVariablePayloadSchema(SQLModel):
    loc: float
    scale: float = Field(gt=0)


class SampleResultSchema(SQLModel):
    s: float


class BinaryOperandsPayloadSchema(SQLModel):
    a: float
    b: float


class BinaryIntegerOperandsPayloadSchema(SQLModel):
    a: int
    b: int


class BinaryOperationResultSchema(SQLModel):
    s: float
