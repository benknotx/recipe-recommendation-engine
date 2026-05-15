from fastapi import FastAPI, Query, HTTPException, Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address as GRA
from slowapi.errors import RateLimitExceeded as RLE
import services.spoonacular_service as spoonacular_service
import schemas
import services.helper as helper
import services.redis_service as redis_service
import httpx
from contextlib import asynccontextmanager
import os
import redis.asyncio as redis
from dotenv import load_dotenv
load_dotenv()



@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.http_client = httpx.AsyncClient()
    app.state.redis_client = redis.Redis(
        host= os.getenv("REDIS_HOST", "localhost"),
        port=int( os.getenv("REDIS_PORT")),
        db=0,
        decode_responses=True)
    yield 
    await app.state.http_client.aclose()
    await app.state.redis_client.close()


app = FastAPI(lifespan = lifespan, title="Recipe Recommendation Engine", version="1.0")
#Initialize the Limiter
limiter = Limiter(key_func=GRA)
app.state.limiter = limiter
@app.exception_handler(RLE)
def rate_limit_handler(request:Request, exc: RLE):
    return JSONResponse(
        status_code= 429,
        content={"Detail": "rate limit exceeded"}
            )


@app.get("/")
def read_root():
    return {"message": "Welcome to the Recipe Recommendation Engine!"}

@app.get("/health")
async def health_check(request: Request):
    client = request.app.state.http_client
    cache = request.app.state.redis_client
    return await helper.health(client, cache)


#metrics reset with application restart
@app.get("/metrics")
def get_metrics():
    return redis_service.get_metrics()



@app.get("/recipes", response_model=list[schemas.recipe_response])
@limiter.limit("5/minute")
async def get_recipes(request: Request, goal:str, ingredients: list[str] = Query(default_factory=list)):
    try:
        if goal not in ["high_protein", "low_carb", "low_fat", "balanced"]:
            raise HTTPException(
                status_code=400, detail="Invalid goal provided. Valid options are: high_protein, low_carb, low_fat, balanced.")
        if not ingredients:
            raise HTTPException(
                status_code=400, detail="Ingredients must be a non-empty list.")
        client = request.app.state.http_client
        cache = request.app.state.redis_client
        recipes = await spoonacular_service.get_recipe_data_by_ingredients(client, cache, ingredients, goal)
        return recipes
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/substitutes", response_model=schemas.substitute_response)
@limiter.limit("10/minute")
async def get_substitutes(request: Request,ingredient: str):
    ingredient = ingredient.strip().lower()
    client = request.app.state.http_client
    if not ingredient:
        raise HTTPException(status_code=400, detail="Ingredient must be a non-empty string.")
    try:
        return await spoonacular_service.substitute_ingredient(client, ingredient)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error: " + str(e))


@app.get("/recipes/goal", response_model=list[schemas.recipe_response])
@limiter.limit("5/minute")
async def get_recipes_by_goal(request:Request,goal:str = "balanced" , ingredients: list[str] = Query(default_factory=list)):
    try:
        if goal not in ["high_protein", "low_carb", "low_fat", "balanced"]:
            raise HTTPException(status_code=400, detail="Invalid goal provided. Valid options are: high_protein, low_carb, low_fat, balanced.")
        client = request.app.state.http_client
        cache = request.app.state.redis_client
        return await spoonacular_service.get_recipe_by_goal(client, cache, ingredients, goal)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error: " + str(e))

@app.get("/recipes/{id}", response_model=schemas.recipe_instructions_response)
@limiter.limit("2/minute")
async def get_recipe_instructions(request: Request, id: int):
    try:
        client = request.app.state.http_client
        return await spoonacular_service.get_recipe_instructions_by_id(client, id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error: " + str(e))
    
