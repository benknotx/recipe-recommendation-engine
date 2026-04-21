# Scoring service for recipe recommendations

# This module contains functions to calculate scores for recipe recommendations based on ingredient matches
def ingredients_match_score(used_ingredient_count, missed_ingredient_count):
    total_ingredients = used_ingredient_count + missed_ingredient_count
    if total_ingredients == 0:
        return 0
    score = used_ingredient_count / total_ingredients
    return round(score, 2)

#this function will calculate a score based on how well the recipe aligns with the user's dietary goal. The scoring is based on
# the percentage of calories from protein, carbs, and fat, and how that aligns with the user's goal
def goal_match_score(percentage_protein, percentage_carbs, percentage_fat, user_goal):
    match user_goal:
        case "high_protein":
            return round((percentage_protein/100)*1.2, 2)
            
        case "low_carb":
            return round((1 - (percentage_carbs/100))*1.1, 2)
            
        case "low_fat":
            return round(1 - (percentage_fat/100), 2)

        case "balanced":
            #40% protein, 30% carbs, 30% fat is a common balanced macronutrient distribution, we can adjust the weights as needed.
            return round((percentage_protein/100)*0.4 + (1 - (percentage_carbs/100))*0.3 + (1 - (percentage_fat/100))*0.3, 2)
    return 0


#this function will calculate an overall score for the recipe based on the ingredient match score and the goal alignment score.
# The weights for each score can be adjusted as needed.
def overall_score(ingredients_score, goal_score, ingredient_weight=0.6, goal_weight=0.4):
    if goal_score == 0:
        return ingredients_score
    return round((ingredients_score * ingredient_weight) + (goal_score * goal_weight), 2)


