import time
from fastapi import HTTPException
from services import helper
from loguru import logger

common_pantry = ["oil", "salt", "pepper", "sugar", "flour", "water", "butter"]
MAX_CACHE_SIZE = 100
TIME_EXPIRATION = 3600  # 1 hour in seconds

cached_recipes = {}


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
    timed_cache_removal()
    cached_recipes[key] = {"data": recipe_data,
                           "timestamp": time.time()}
    size_cache_removal()


def get_cache_by_key(goal,ingredients=[], offset=0):
    timed_cache_removal()
    key = generate_cache_key(goal,ingredients, offset)
    if key not in cached_recipes:
        logger.info("Cache miss")
        return None
    logger.info(f"Cache hit: {key}")
    return cached_recipes[key]["data"]


def clear_cache():
    cached_recipes.clear()

def timed_cache_removal():
    current_time = time.time()
    keys_to_remove = []
    for key, value in cached_recipes.items():
        if current_time - value["timestamp"] > TIME_EXPIRATION:
            keys_to_remove.append(key)
    for key in keys_to_remove:
        del cached_recipes[key]

def size_cache_removal():
    if len(cached_recipes) > MAX_CACHE_SIZE:
        sorted_cache = sorted(cached_recipes.items(), key=lambda item: item[1]["timestamp"])
        keys_to_remove = [key for key, value in sorted_cache[:len(cached_recipes) - MAX_CACHE_SIZE]]
        for key in keys_to_remove:
            del cached_recipes[key]

