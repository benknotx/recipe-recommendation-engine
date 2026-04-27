from fastapi import HTTPException
from services import helper
from loguru import logger
import redis
import json
import os
from dotenv import load_dotenv
load_dotenv()


common_pantry = ["oil", "salt", "pepper", "sugar", "flour", "water", "butter"]
TIME_EXPIRATION = 3600


redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT")),
    db=0,
    decode_responses=True
)

def clean_filter_ingredients(ingredients):
    cleaned_list = helper.ingredient_normalization(ingredients)
    filtered_list = [i for i in cleaned_list if i not in common_pantry]
    final_list = list(sorted((set(filtered_list))))
    return final_list


def generate_cache_key(goal, ingredients=None, offset=0):
    if ingredients:
        filtered_list = clean_filter_ingredients(ingredients)
        if not filtered_list:
            raise HTTPException(
                status_code=400,
                detail="No valid ingredients provided after filtering common pantry items."
            )
        key = "_".join(filtered_list) + f"_{goal}"
    else:
        key = f"goal::{goal}::offset_{offset}"   
    return key
  

def add_to_cache(key, recipe_data):
    redis_client.setex(
        key,
        TIME_EXPIRATION,
        json.dumps(recipe_data)
    )
   


def get_cache_by_key(goal,ingredients=None, offset=0):
    key = generate_cache_key(goal,ingredients, offset)
    logger.info(f"{key}")
    data = redis_client.get(key)
    if not data:
        logger.info(f"Cache MISS: {key}")
        return None
    logger.info(f"Cache hit: {key}")
    return json.loads(data)