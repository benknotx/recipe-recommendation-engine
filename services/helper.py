from fastapi import APIRouter
import os
import dotenv
from loguru import logger
dotenv.load_dotenv()
Spoon_KEY = os.getenv('SPOON_KEY')

URL = "https://api.spoonacular.com/recipes/complexSearch"



def ingredient_normalization(ingredients):
    result = []
    for item in ingredients:
        result.extend([i.strip().lower() for i in str(item).split(',')])
    return result

def goal_normalization_for_complex(goal):
    goal_mapping = {
    # high protein is considered to be ~20% of daily 2000 calories from protein
    # that is about 100 grams of protein per day divide that by 3 meals and we get around 33 grams of protein per meal
        "high_protein": "minProtein=33",
    # low carb is considered to be 65 grams of carbs per day divide that by 3 meals and we get around 20 grams of carbs per meal    
        "low_carb": "maxCarbs=20",
    # lowfat is considered to be 44-78 grams per day divide that by 3 meals and we get around 15-25 grams of fat per meal    
        "low_fat": "maxFat=20",
    # a balanced meal is conidered to be about 40-40-30 split by percent, 
    # to implement this we will will assume a 2000 calorie diet and calculate the grams of each macronutrient based on that
    # then divide by 3 meals to get the per meal target
        "balanced": "minProtein=20&maxProtein=40&maxCarbs=60&maxFat=20"
    }
    #we could also sort by diet name type such as keto, vegetarian, vegan, etc but for now we will focus on the macronutrient goals
    return goal_mapping.get(goal, None)


async def health(client, cache):
    status = {"API": "OK",
              "REDIS": "OK",
              "SPOONACULAR": "OK"  }
    try: 
        await cache.ping()
        status["REDIS"] = "OK"
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        status["REDIS"] = "DOWN"
    try:
        response = await client.get(
            URL,
            params={
                "apiKey": Spoon_KEY,
                "number": 1
            },
            timeout=3
        )
        if response.status_code == 200:
            status["SPOONACULAR"] = "OK"
        else:
            status["SPOONACULAR"] = "degraded"
    except Exception as e:
        logger.error(f"Spoonacular health check failed: {e}")
        status["SPOONACULAR"] = "down"
    
    logger.info(f"status = {status}")
    return status

