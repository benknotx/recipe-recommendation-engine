from random import random, choice
import os
import dotenv
from fastapi import HTTPException
import services.helper as helper
import services.redis_service as redis_service
import services.scoring_service as scoring_service
from loguru import logger
dotenv.load_dotenv()
Spoon_KEY = os.getenv('SPOON_KEY') 
number_of_recipes = 1

async def substitute_ingredient(client, ingredient):
    url = f"https://api.spoonacular.com/food/ingredients/substitutes?ingredientName={ingredient}&apiKey={Spoon_KEY}"
    response = await client.get(url)
    if response.status_code == 200:
        data = response.json()
        substitutes = data.get('substitutes', [])
        if data.get('status') == 'failure':
            raise HTTPException(status_code=400, detail=f"No substitutes found for ingredient: {ingredient}")
        return {"substitutes": substitutes}
    else:
        raise HTTPException(status_code=response.status_code, detail=f"Error: {response.text}")
    
def normalize_recipe_data(recipe_data, goal, ingredients = []):
    normalized_data = []
    for recipe in recipe_data:
        ingredient_score = goal_score = 0
        calories = carbs= fat = protein = percentage_protein = percentage_carbs = percentage_fat = goal_score = 0
        recipe_id = recipe['id']
        recipe_title = recipe['title']
        nutrition_data = recipe.get('nutrition',{})
        if nutrition_data:
            ingredients_list = get_recipe_ingredients(nutrition_data.get("nutrition",{}))
            ingredient_score = get_ingredient_score(ingredients, ingredients_list) 
        if nutrition_data is not None:
            nutrition_data = nutrition_data
            nutrients = nutrition_data.get("nutrition", {}).get("nutrients",[])
            nutrient_map = {item["name"]: item["amount"] for item in nutrients}
            calories = nutrient_map.get('Calories', 0)
            carbs = nutrient_map.get('Carbohydrates', 0)
            fat = nutrient_map.get('Fat', 0)
            protein = nutrient_map.get('Protein', 0)
            percentages = nutrition_data.get("nutrition",{}).get('caloricBreakdown', {})
            percentage_protein = percentages.get('percentProtein', 0)
            percentage_carbs = percentages.get('percentCarbs', 0)
            percentage_fat = percentages.get('percentFat', 0)
            goal_score = scoring_service.goal_alignment_score(percentage_protein, percentage_carbs, percentage_fat, goal)

#now we have all the data to append to the dictionary that we will return to the user and cache
        normalized_data.append(
            {
            'id': recipe_id,
            'title': recipe_title,
            'match_score': ingredient_score,
            'goal_alignment_score': goal_score,
            'calories': calories,
            'carbs': carbs,
            'fat': fat,
            'protein': protein,
            'percentage_protein': percentage_protein,
            'percentage_carbs': percentage_carbs,
            'percentage_fat': percentage_fat,
            'overall_score': scoring_service.overall_score(ingredient_score, goal_score)
#extra items we may want later
            #'image': recipe['image'],
            #'usedIngredients': [ingredient['name'] for ingredient in recipe['usedIngredients']],
            #'missedIngredients': [ingredient['name'] for ingredient in recipe['missedIngredients']]
            })
    return normalized_data


#api call to spoonacular for the data and then process the data to return the relevant information to the user.
async def get_recipe_data_by_ingredients(client, cache, ingredients, goal):
    cleaned_list = helper.ingredient_normalization(ingredients)
    ingredients_query = ','.join(cleaned_list)
    recipe_url = f"https://api.spoonacular.com/recipes/findByIngredients?ingredients={ingredients_query}&number={number_of_recipes}&apiKey={Spoon_KEY}"
    cached_data = await redis_service.get_cache_by_key(cache, goal, cleaned_list)
    if cached_data is not None:
        return cached_data
    response = await client.get(recipe_url)
    
    if response.status_code == 200:
        recipe_data = response.json()
        recipe_ids = [recipe['id'] for recipe in recipe_data]
        logger.info("post recipe id")
        nutrition_data = await get_nutrition_bulk(client, recipe_ids)
        recipe_data = map_nutrition_to_recipe(recipe_data, nutrition_data)
        key = redis_service.generate_cache_key(goal, cleaned_list)
        recipe_data = normalize_recipe_data(recipe_data, goal, ingredients)
        logger.info("Fetching from Spoonacular API")
        recipe_data = sorted(recipe_data, key=lambda x: x["overall_score"], reverse=True)
        await redis_service.add_to_cache(cache, key, recipe_data)
        return recipe_data[:3]
    else:
        raise HTTPException(status_code=response.status_code, detail=f"Error: {response.text}")
    
    
async def get_nutrition_bulk(client, recipe_ids: list[int]):
    bulk_url = f"https://api.spoonacular.com/recipes/informationBulk?ids={','.join(map(str,recipe_ids))}&includeNutrition=true&apiKey={Spoon_KEY}"
    response = await client.get(bulk_url)
    if response.status_code ==200:
        data = response.json()
        return data
    else:
        raise HTTPException(status_code=response.status_code, detail=f"Error: {response.txt}")

def map_nutrition_to_recipe(recipe_data, nutrition_data):
    nutrition_map= { item['id']: item  for item in nutrition_data}
    for recipe in recipe_data:
        recipe_id = recipe["id"]
        recipe["nutrition"] = nutrition_map.get(recipe_id)
    return recipe_data

async def get_recipe_instructions_by_id(client, recipe_id):
    url = f"https://api.spoonacular.com/recipes/{recipe_id}/information?includeNutrition=false&apiKey={Spoon_KEY}"
    response = await client.get(url)
    if response.status_code == 200:
        data = response.json()
        instructions = data.get('instructions', '')
        ingredients = [ingredient['original'] for ingredient in data.get('extendedIngredients', [])]
        return {
            'id': recipe_id,
            'title': data.get('title', ''),
            'servings': data.get('servings', 0),
            'ingredients': ingredients,
            'instructions': instructions
        }
    else:
        raise HTTPException(status_code=response.status_code, detail=f"Error: {response.text}")
    
async def get_recipe_by_goal(client, cache, ingredients, goal = "balanced"):
    goal_param = helper.goal_normalization_for_complex(goal)
    offset = choice([0,5,10,15,20,25,30])
    url = f"https://api.spoonacular.com/recipes/complexSearch?{goal_param}&number={number_of_recipes}&offset={offset}&apiKey={Spoon_KEY}"
    cached_data = await redis_service.get_cache_by_key(cache, goal, offset=offset)
    if cached_data is not None:
        return cached_data
    response = await client.get(url)
    if response.status_code == 200:
        recipe_data = response.json()
        recipe_data = recipe_data.get("results",[])
        recipe_ids = [recipe['id'] for recipe in recipe_data]
        nutrition_data = await get_nutrition_bulk(client, recipe_ids)
        recipe_data = map_nutrition_to_recipe(recipe_data, nutrition_data)
        key = redis_service.generate_cache_key(goal, offset=offset)
        recipe_data = normalize_recipe_data(recipe_data, goal, ingredients)
        recipe_data = sorted(recipe_data, key=lambda x: x["overall_score"], reverse=True)
        await redis_service.add_to_cache(cache, key, recipe_data)
        return recipe_data[:3]
    else:
        raise HTTPException(status_code=response.status_code, detail=f"Error: {response.text}")
    
def get_ingredient_score(input_ingredients, recipe_ingredients):
    input_set = set(input_ingredients)
    recipe_set = set(recipe_ingredients)
    used_ingredient_count = len(input_set.intersection(recipe_set))
    missed_ingredient_count = len(recipe_set.difference(input_set))
    return scoring_service.ingredients_match_score(used_ingredient_count, missed_ingredient_count, len(input_set))


def get_recipe_ingredients(recipe_data):
    ingredients = [ingredient['name'] for ingredient in recipe_data.get('ingredients', [])]
    return list(sorted(set(ingredients)))
