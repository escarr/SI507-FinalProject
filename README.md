# SI507-FinalProject

Project Description: My final project is a tool to help people find and store recipes in a database, as well as to analyze the nutritional content of the recipes. Therefore, the project is aimed at those who like to cook and want to have more access to the nutritional composition of their food.

Data Sources--The following data sources were used for this project:

(1)	The user can enter the URL to a recipe from allrecipes.com. In this case, the program scrapes the HTML returned to get information about the recipe (such as the recipe title and category) and the nutrition facts of the recipe (calories, fat, carbohydrates, protein, cholesterol, and sodium). If the recipe is not already in the recipe database, it will add it.

Example recipe from allrecipes.com: https://www.allrecipes.com/recipe/228129/classic-savory-deviled-eggs/?internalSource=streams&referringId=110&referringContentType=Recipe%20Hub&clickId=st_trending_b

(2)	The user can enter a search term (such as “burger”) and the program will make a request to the spoonacular API to find recipes using their “Search Recipes” functionality. If the user picks this option, it will print out the list of recipes returned by the API for the user to choose from. Then, the program will make a call to the spoonacular API “Get Recipe Information” to get the URL for the recipe and to the "Visualize Recipe Nutrition by id” functionality to get the nutrition facts for the recipe chosen by the user. If the recipes are not already in the recipe database, it will add it.

Links to the spoonacular endpoints I will be using: https://rapidapi.com/spoonacular/api/recipe-food-nutrition?endpoint=55e1b24ae4b0a29b2c36073c https://rapidapi.com/spoonacular/api/recipe-food-nutrition?endpoint=55e1ba5ee4b0a29b2c360756 https://rapidapi.com/spoonacular/api/recipe-food-nutrition?endpoint=596be6e5e4b02ae5957fb3ad

Code Structure--The code is structured in the following format:

1. Caching code for the results returned by the spoonacular API and the HTML returned from the allrecipes url (the caching file is named 'recipes.json')
2. For recipes found using the spoonacular API, the combine_recipe_info(search_term) function is used to get the needed information in order to populate the database--it will call the appropiate functions to get a list of recipes from the spoonacular API along with the nutritional information and url for each
3. For recipes from allrecipes.com, the scrape_website_url(url) function is used to get the needed information to populate the database by scraping the HTML returned
4. 'recipes' is the dictionary of new recipes to be added to the database; the combine_recipe_info(search_term) and scrape_website_url(url) functions will add the recipes to this dictionary which insert_stuff() will use to add the recipes to the database
5. In terms of the database, it is named 'recipes.db'--the init_db() function will create the database and pre-populate it with some recipes and insert_stuff() will add new recipes to the database (note: add --init like 'python3 final_project.py --init' in order to call the init_db() function, must include this first time running the program; otherwise the program will just add the new recipes to the database)
6. The code within 'if name == "main":' supports the interactive command line prompt

User Guide: The user is first asked if they would like to (1) enter the URL of a recipe from allrecipes.com, (2) make a request to the spoonacular API, (3) retrieve a recipe already in their recipe database or (4) ask the program to randomly pick a recipe from their recipe database for them (for when they can’t decide what to eat!). After the user has selected a recipe, it asks them how they would like the recipe information to be presented to them. An interactive command line prompt will be built to support this. Visualization options include: (1)	A text file with the recipe information nicely formatted (it will print it as well) (2)	Launch the URL of the recipe in a web browser (3)	Data visualization of the nutrition facts created using plotly: a pie chart of the macronutrient breakdown by number of calories (carbs vs. protein vs. fat) (4) Compare the nutrition facts of two recipes by using plotly to create side-by-side bar graphs of the calories, macronutrients and sodium/cholesterol.

Note: help text is provided to help the user know what to enter/how to format it.
