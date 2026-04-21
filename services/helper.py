

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
    # low carb is considered to be 130 grams of carbs per day divide that by 3 meals and we get around 43 grams of carbs per meal    
        "low_carb": "maxCarbs=40",
    # lowfat is considered to be 44-78 grams per day divide that by 3 meals and we get around 15-25 grams of fat per meal    
        "low_fat": "maxFat=20",
    # a balanced meal is conidered to be about 40-40-30 split by percent, 
    # to implement this we will will assume a 2000 calorie diet and calculate the grams of each macronutrient based on that
    # then divide by 3 meals to get the per meal target
        "balanced": "minProtein=20&maxProtein=40&maxCarbs=60&maxFat=20"
    }
    #we could also sort by diet name type such as keto, vegetarian, vegan, etc but for now we will focus on the macronutrient goals
    return goal_mapping.get(goal, None)
