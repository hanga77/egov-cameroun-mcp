from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    history: list[ChatMessage] = Field(default_factory=list)


class ToolCall(BaseModel):
    tool_name: str
    input: dict
    output: str


class ChatResponse(BaseModel):
    message: str
    tool_calls: list[ToolCall] = Field(default_factory=list)


class Employee(BaseModel):
    name: str
    gross_salary: float = Field(..., gt=0, description="Salaire brut mensuel en FCFA")


class CNPSContributionsRequest(BaseModel):
    employees: list[Employee] = Field(..., min_length=1)


class VATRequest(BaseModel):
    revenue_ht: float = Field(..., gt=0, description="Chiffre d'affaires HT en FCFA")
    period: str = Field(..., pattern=r"^\d{4}-\d{2}$", description="Période YYYY-MM")


class StatisticsRequest(BaseModel):
    indicator: str = Field(..., description="Code indicateur World Bank (ex: NY.GDP.MKTP.CD)")
    start_year: int = Field(default=2020, ge=2000, le=2030)
    end_year: int = Field(default=2023, ge=2000, le=2030)
