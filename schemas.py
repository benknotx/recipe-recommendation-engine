from pydantic import BaseModel

class recipe_options(BaseModel):
    id: int
    title: str

class recipe_response(BaseModel):
    id: int
    title: str
    match_score: float
    goal_alignment_score: float
    overall_score: float
    calories: float
    carbs: float
    fat: float
    protein: float
    percentage_protein: float
    percentage_carbs: float
    percentage_fat: float

class recipe_request(BaseModel):
    ingredients: list[str]
    goal: str = "balanced"

class substitute_response(BaseModel):
    ingredient: str
    substitutes: list[str]

class recipe_instructions_response(BaseModel):
    id: int
    title: str
    servings: int
    ingredients: list[str]
    instructions: str
    