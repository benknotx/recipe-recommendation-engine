from fastapi import FastAPI, Query, HTTPException
import services.spoonacular_service as spoonacular_service
import schemas
import services.helper as helper
import services.redis_service as redis_service


app = FastAPI(title="Recipe Recommendation Engine", version="1.0")



@app.get("/")
def read_root():
    return {"message": "Welcome to the Recipe Recommendation Engine!"}

@app.get("/health")
async def health_check():
     return await helper.health()

@app.get("/metrics")
def get_metrics():
    return redis_service.get_metrics()



@app.get("/recipes", response_model=list[schemas.recipe_response])
async def get_recipes(goal:str, ingredients: list[str] = Query(default_factory=list)):
    try:
        if goal not in ["high_protein", "low_carb", "low_fat", "balanced"]:
            raise HTTPException(
                status_code=400, detail="Invalid goal provided. Valid options are: high_protein, low_carb, low_fat, balanced.")
        if not ingredients:
            raise HTTPException(
                status_code=400, detail="Ingredients must be a non-empty list.")
        recipes = await spoonacular_service.get_recipe_data_by_ingredients(ingredients, goal)
        return recipes
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/substitutes", response_model=schemas.substitute_response)
async def get_substitutes(ingredient: str):
    ingredient = ingredient.strip().lower()
    if not ingredient:
        raise HTTPException(status_code=400, detail="Ingredient must be a non-empty string.")
    try:
        return await spoonacular_service.substitute_ingredient(ingredient)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error: " + str(e))


@app.get("/recipes/goal", response_model=list[schemas.recipe_response])
async def get_recipes_by_goal(goal:str = "balanced" , ingredients: list[str] = Query(default_factory=list)):
    try:
        if goal not in ["high_protein", "low_carb", "low_fat", "balanced"]:
            raise HTTPException(status_code=400, detail="Invalid goal provided. Valid options are: high_protein, low_carb, low_fat, balanced.")
        return await spoonacular_service.get_recipe_by_goal(ingredients, goal)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error: " + str(e))

@app.get("/recipes/{id}", response_model=schemas.recipe_instructions_response)
async def get_recipe_instructions(id: int):
    try:
        return await spoonacular_service.get_recipe_instructions_by_id(id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error: " + str(e))
    
