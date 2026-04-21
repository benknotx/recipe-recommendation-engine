from random import random, choice
import requests
import os
import dotenv
from fastapi import HTTPException
import services.helper as helper
import services.cache_service as cache_service
import services.scoring_service as scoring_service
from loguru import logger
dotenv.load_dotenv()
Spoon_KEY = os.getenv('SPOON_KEY') 


def substitute_ingredient(ingredient):
    url = f"https://api.spoonacular.com/food/ingredients/substitutes?ingredientName={ingredient}&apiKey={Spoon_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        substitutes = data.get('substitutes', [])
        if data.get('status') == 'failure':
            raise HTTPException(status_code=400, detail=f"No substitutes found for ingredient: {ingredient}")
        return substitutes
    else:
        raise HTTPException(status_code=response.status_code, detail=f"Error: {response.text}")
    
def normalize_recipie_data(recipe_data, goal, ingredients = []):
    normalized_data = []
    for recipe in recipe_data:
        ingredient_score = goal_score = 0
        calories = carbs= fat = protein = percentage_protein = percentage_carbs = percentage_fat = goal_score = 0
        recipe_id = recipe['id']
        recipe_title = recipe['title']
        nutrition_data = recipe.get('nutrition')
        if nutrition_data:
            ingredients_list = get_ingredients_list(recipe_data)
            ingredient_score = get_ingredient_score(ingredients, ingredients_list) 
        if not nutrition_data:
            nutrition_data = get_recipe_data_by_id(recipe_id)
            ingredient_score = scoring_service.ingredients_match_score(recipe.get('usedIngredientCount', 0), recipe.get('missedIngredientCount', 0))
        if nutrition_data is not None:
            nutrition_data = nutrition_data
            nutrients = nutrition_data.get("nutrients", [])
            nutrient_map = {item["name"]: item["amount"] for item in nutrients}
            calories = nutrient_map.get('Calories', 0)
            carbs = nutrient_map.get('Carbohydrates', 0)
            fat = nutrient_map.get('Fat', 0)
            protein = nutrient_map.get('Protein', 0)
            percentages = nutrition_data.get('caloricBreakdown', {})
            percentage_protein = percentages.get('percentProtein', 0)
            percentage_carbs = percentages.get('percentCarbs', 0)
            percentage_fat = percentages.get('percentFat', 0)
            goal_score = scoring_service.goal_match_score(percentage_protein, percentage_carbs, percentage_fat, goal)

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
def get_recipe_data_by_ingredients(ingredients, goal, number_of_recipes = 2):
    cleaned_list = helper.ingredient_normalization(ingredients)
    ingredients_query = ','.join(cleaned_list)
    url = f"https://api.spoonacular.com/recipes/findByIngredients?ingredients={ingredients_query}&number={number_of_recipes}&apiKey={Spoon_KEY}"
    cached_data = cache_service.get_cache_by_key(cleaned_list, goal)
    if cached_data is not None:
        return cached_data
    response = requests.get(url)
    if response.status_code == 200:
        recipie_data = response.json()
        key = cache_service.generate_cache_key(goal, cleaned_list)
        recipe_data = normalize_recipie_data(recipie_data, goal)
        logger.info("Fetching from Spoonacular API")
        recipe_data = sorted(recipe_data, key=lambda x: x["overall_score"], reverse=True)
        cache_service.add_to_cache(key, recipe_data)
        return recipe_data[:3]
    else:
        raise HTTPException(status_code=response.status_code, detail=f"Error: {response.text}")
    
#call the spoonacular api to get the recipe nutrition data by id
def get_recipe_data_by_id(recipe_id):
    url = f"https://api.spoonacular.com/recipes/{recipe_id}/nutritionWidget.json?apiKey={Spoon_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data
    else:
        raise HTTPException(status_code=response.status_code, detail=f"Error: {response.text}")
    

def get_recipe_instructions_by_id(recipe_id):
    url = f"https://api.spoonacular.com/recipes/{recipe_id}/information?includeNutrition=false&apiKey={Spoon_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        instructions = data.get('instructions', '')
        ingredients = [ingredient['name'] for ingredient in data.get('extendedIngredients', [])]
        return {
            'id': recipe_id,
            'title': data.get('title', ''),
            'servings': data.get('servings', 0),
            'ingredients': ingredients,
            'instructions': instructions
        }
    else:
        raise HTTPException(status_code=response.status_code, detail=f"Error: {response.text}")
    

def get_recipe_by_goal(ingredients, goal = "balanced"):
    goal_param = helper.goal_normalization_for_complex(goal)
    offset = choice([0, 5, 10, 15, 20, 25, 30])
    url = f"https://api.spoonacular.com/recipes/complexSearch?{goal_param}&number=3&offset={offset}&addRecipeNutrition=true&addRecipeInstructions=true&apiKey={Spoon_KEY}"
    cached_data = cache_service.get_cache_by_key(goal, offset=offset)
    if cached_data is not None:
        return cached_data
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        key = cache_service.generate_cache_key(goal, offset=offset)
        recipe_data = normalize_recipie_data(data.get('results', []), goal, ingredients)
        logger.info("Fetching from Spoonacular API")
        recipe_data = sorted(recipe_data, key=lambda x: x["overall_score"], reverse=True)
        cache_service.add_to_cache(key, recipe_data)
        return recipe_data[:3]
    else:
        raise HTTPException(status_code=response.status_code, detail=f"Error: {response.text}")
    
def get_ingredients_list(data):
    for recipe in data:
        nutrition = recipe.get('nutrition', {})
        ingredients = nutrition.get('ingredients', [])
    ingredients_list = [item.get("name", "").lower() for item in ingredients]
    return list(sorted(set(ingredients_list)))

def get_ingredient_score(input_ingredients, recipe_ingredients):
    input_set = set(input_ingredients)
    recipe_set = set(recipe_ingredients)
    used_ingredient_count = len(input_set.intersection(recipe_set))
    missed_ingredient_count = len(recipe_set.difference(input_set))
    return scoring_service.ingredients_match_score(used_ingredient_count, missed_ingredient_count)
