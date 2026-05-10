from fastapi import HTTPException
from services import helper
from loguru import logger
import redis.asyncio as redis
import json
import os
from dotenv import load_dotenv
load_dotenv()


common_pantry = ["oil", "salt", "pepper", "sugar", "flour", "water", "butter"]
TIME_EXPIRATION = 3600
HITS=0
MISSES=0

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
  

async def add_to_cache(key, recipe_data):
    await redis_client.setex(
        key,
        TIME_EXPIRATION,
        json.dumps(recipe_data)
    )
   


async def get_cache_by_key(goal,ingredients=None, offset=0):
    key = generate_cache_key(goal,ingredients, offset)
    data = await redis_client.get(key)
    if not data:
        logger.info(f"Cache MISS: {key}")
        global MISSES
        MISSES +=1
        return None
    logger.info(f"Cache hit: {key}")
    global HITS
    HITS +=1
    return json.loads(data)

def get_metrics():
    global HITS, MISSES
    return {"Cache_hits": HITS,
            "Cache_misses": MISSES,
            "Hit_Ratio": str(round( HITS / (HITS+MISSES))*100, 2)+("%")  if HITS > 0 and MISSES >0 else 0
            }