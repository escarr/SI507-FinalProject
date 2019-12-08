import requests
import json
import sqlite3
from secrets import spoonacular_api_key
from bs4 import BeautifulSoup
import webbrowser
import plotly
import plotly.graph_objs as go
import sys
import random
import pandas as pd
from tabulate import tabulate

# must have an api key from spoonacular
api_key = spoonacular_api_key


# CACHING FUNCTION FOR SPOONACULAR API RESULTS/SCRAPING ALLRECIPES.COM

CACHE_FNAME = 'recipes_cache.json'

try:
    cache_file = open(CACHE_FNAME, 'r')
    cache_contents = cache_file.read()
    CACHE_DICTION = json.loads(cache_contents)
    cache_file.close()
except:
    CACHE_DICTION = {}

def params_unique_combination(baseurl, params):
    try:
        alphabetized_keys = sorted(params.keys())
        res = []
        for k in alphabetized_keys:
            res.append("{}-{}".format(k, params[k]))
        return baseurl + "_" + "_".join(res)
    except:
        return baseurl

def make_request_using_cache(baseurl, params, headers):
    unique_ident = params_unique_combination(baseurl,params)

    if unique_ident in CACHE_DICTION:
        return CACHE_DICTION[unique_ident]

    else:
        ##print("Making new request...")
        resp = requests.get(baseurl, params = params, headers=headers)
        CACHE_DICTION[unique_ident] = json.loads(resp.text)
        dumped_json_cache = json.dumps(CACHE_DICTION)
        fw = open(CACHE_FNAME,"w")
        fw.write(dumped_json_cache)
        fw.close() 
        return CACHE_DICTION[unique_ident]

def make_request_using_cache2(baseurl, params, headers):
    unique_ident = params_unique_combination(baseurl,params)

    if unique_ident in CACHE_DICTION:
        return CACHE_DICTION[unique_ident]

    else:
        ##print("Making new request...")
        resp = requests.get(baseurl, params = params, headers=headers)
        CACHE_DICTION[unique_ident] = resp.text
        dumped_json_cache = json.dumps(CACHE_DICTION)
        fw = open(CACHE_FNAME,"w")
        fw.write(dumped_json_cache)
        fw.close() 
        return CACHE_DICTION[unique_ident]


# RECIPES DICTIONARY -- WILL USE TO ADD NEW RECIPES TO THE DATABASE

recipes = {}

# if the recipe is not already in the dictionary, add it
def add_recipe(recipe_info):
    if recipe_info["title"] in recipes:
        pass
    else:
        recipes[recipe_info["title"]] = recipe_info

# ------------------------------SPOONACULAR------------------------------
# spoonacular API - search for recipes by keyword
# parameters:
# (1) search term
# returns a list of recipes -- each recipe is a dictionary with the:
# (1) title
# (2) id
# (3) category

def search_for_recipes(search_term):
    url = "https://spoonacular-recipe-food-nutrition-v1.p.rapidapi.com/recipes/search"
    headers={"x-rapidapi-key": api_key,
        "x-rapidapi-host": "spoonacular-recipe-food-nutrition-v1.p.rapidapi.com"}
    params = { "query" : search_term }

    r = make_request_using_cache(url, params, headers)
    recipes = []
    for recipe in r["results"]:
        recipes.append ( { "title" : recipe["title"], "id" : recipe["id"], "category" : search_term } )
    return recipes


# spoonacular API - get nutritional information for a recipe
# parameters:
# (1) Recipe id
#returns a dictionary of the nutritional information for the recipe including:
# (1) Calories
# (2) Protein
# (3) Fat
# (4) Carbohydrates
# (5) Sodium
# (6) Cholesterol

def get_nutritional_information(recipe_id):

    url = "https://spoonacular-recipe-food-nutrition-v1.p.rapidapi.com/recipes/{}/nutritionWidget".format(recipe_id)

    headers = {
        'x-rapidapi-host': "spoonacular-recipe-food-nutrition-v1.p.rapidapi.com",
        'x-rapidapi-key': api_key,
        'accept': "text/html" }

    r = make_request_using_cache2(url, params=None, headers=headers)
    page_soup = BeautifulSoup(r, 'html.parser')
    tags = page_soup.find_all(class_="spoonacular-nutrient-name")
    values = page_soup.find_all(class_="spoonacular-nutrient-value")

    nutrient_info = {}
    for nutrient in range(len(tags)):
        value = values[nutrient].text
        if tags[nutrient].text.strip() in ["Calories", "Protein", "Fat", "Carbohydrates", "Sodium", "Cholesterol"]:
            if "mg" in value:
                nutrient_info[tags[nutrient].text.strip()] = float((values[nutrient].text).strip("mg"))
            elif "g" in value:
                nutrient_info[tags[nutrient].text.strip()] = float((values[nutrient].text).strip("g"))
            else:
                nutrient_info[tags[nutrient].text.strip()] = int(values[nutrient].text)
    return nutrient_info


# spoonacular API - get the url for the recipe
# parameters:
# (1) Recipe ID
# returns the url for the recipe

def get_recipe_url(recipe_id):
    url = "https://spoonacular-recipe-food-nutrition-v1.p.rapidapi.com/recipes/{}/information".format(recipe_id)

    headers = {
        'x-rapidapi-host': "spoonacular-recipe-food-nutrition-v1.p.rapidapi.com",
        'x-rapidapi-key': api_key }

    r = make_request_using_cache(url, params=None, headers=headers)
    return r["sourceUrl"]


# for recipes from spoonacular, combine the recipe information and add the new recipes to the new recipes dictionary

def combine_recipe_info(search_term):
    recipes = search_for_recipes(search_term)
    for recipe in recipes:
        recipe_id = recipe["id"]
        nutrition_info = get_nutritional_information(recipe_id)
        url = get_recipe_url(recipe_id)
        recipe_info = {"title": recipe["title"], "category": recipe["category"], "url": url, "nutrition" : nutrition_info}
        add_recipe(recipe_info) 


# ------------------------------ALLRECIPES.COM------------------------------

# function to scrape HTML returned from allrecipes.com
# will add the recipe to the new recipes dictionary

def scrape_recipe_website(url):
    r = make_request_using_cache2(url, params=None, headers=None)
    page_soup = BeautifulSoup(r, 'html.parser')
    recipe_title = page_soup.find(id = "recipe-main-content", itemprop = "name").text.strip()
    category = page_soup.find_all(itemprop = "itemListElement")[-2].text.strip()
    calories = int(page_soup.find(itemprop = "calories").text.split(" ")[0])
    fat = float(page_soup.find(itemprop = "fatContent").text)
    carbs = float(page_soup.find(itemprop = "carbohydrateContent").text)
    protein = float(page_soup.find(itemprop = "proteinContent").text)
    cholesterol = int(page_soup.find(itemprop = "cholesterolContent").text)
    sodium = int(page_soup.find(itemprop = "sodiumContent").text)
    recipe_info = {"title": recipe_title, "category": category, "url": url, "nutrition": {"Calories": calories, "Fat": fat, "Carbohydrates": carbs, 
    "Protein": protein, "Cholesterol": cholesterol, "Sodium": sodium }}
    add_recipe(recipe_info) 


# CREATE THE DATABASE
DBNAME = 'recipes.db'

# initalize the database
def init_db():

    # connect to database and create cursor
    conn = sqlite3.connect(DBNAME)
    cur = conn.cursor()

    # drop tables if they exist
    statement = '''
        DROP TABLE IF EXISTS 'Category';
    '''

    cur.execute(statement)

    statement = '''
        DROP TABLE IF EXISTS 'Recipe';
    '''

    cur.execute(statement)
    conn.commit()

    # create the tables 
    statement = '''
        CREATE TABLE 'Category' (
            'Id' INTEGER PRIMARY KEY AUTOINCREMENT,
            'Name' TEXT
        )
    '''
    cur.execute(statement)

    statement = '''
        CREATE TABLE 'Recipe' (
            'Id' INTEGER PRIMARY KEY AUTOINCREMENT,
            'Title' TEXT,
            'Calories' INTEGER,
            'Fat' REAL,
            'Carbohydrates' REAL,
            'Protein' REAL,
            'Cholesterol' REAL,
            'Sodium' REAL,
            'URL' TEXT,
            'CategoryId' INTEGER,
            FOREIGN KEY(CategoryId) REFERENCES Category(Id)
        )
    '''
    cur.execute(statement)
    conn.commit()

    #pre-populate the database with some recipes
    combine_recipe_info("burger")
    scrape_recipe_website("https://www.allrecipes.com/recipe/228129/classic-savory-deviled-eggs/?internalSource=streams&referringId=110&referringContentType=Recipe%20Hub&clickId=st_trending_b")
    insert_stuff()

    conn.commit()
    conn.close()
    

# insert new recipes into the database from the new recipes dictionary

def insert_stuff():

    # connect to database and create a cursor
    conn = sqlite3.connect(DBNAME)
    cur = conn.cursor()
    
    # recipes is the dictionary of new recipes 

    # add the category to the Category table, if not already in it  
    for recipe in recipes:

        statement = '''
        SELECT Name
        FROM Category
        '''
        cur.execute(statement)
        current_categories = []
        for row in cur:
            current_categories.append(row[0])

        if recipes[recipe]["category"] not in current_categories:
            insertion = (None, recipes[recipe]["category"])
            statement = 'INSERT INTO "Category" '
            statement += 'VALUES (?, ?)'
            cur.execute(statement, insertion)

    # add the recipe(s) to the Recipes table, if not already in it
    for recipe in recipes:

        statement = '''
        SELECT Title
        FROM Recipe
        '''
        cur.execute(statement)
        current_recipes = []
        for row in cur:
            current_recipes.append(row[0])

        if recipes[recipe]["title"] not in current_recipes:

            # get the value of the foreign key for the Category
            statement = 'SELECT Id FROM Category WHERE Name = "' + recipes[recipe]["category"] + '"'
            cur.execute(statement)
            for c in cur:
                category_id = c[0]
                 
            # columns:'Id', 'Title', 'Calories', 'Fat', 'Carbohydrates', 'Protein', 'Cholesterol' 'Sodium', 'URL', 'Category'
            insertion = (None, recipe, recipes[recipe]["nutrition"]["Calories"], recipes[recipe]["nutrition"]["Fat"],
                recipes[recipe]["nutrition"]["Carbohydrates"], recipes[recipe]["nutrition"]["Protein"], recipes[recipe]["nutrition"]["Cholesterol"],
                recipes[recipe]["nutrition"]["Sodium"], recipes[recipe]["url"], category_id)

            statement = 'INSERT INTO "Recipe" '
            statement += 'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'
            cur.execute(statement, insertion)

    conn.commit()
    conn.close()


# only clear the database if user passes in '--init
# otherwise, just add the new recipes to the database
if len(sys.argv) > 1 and sys.argv[1] == '--init':
    print('Deleting db and starting over from scratch.')
    init_db()
else:
    print('Leaving the DB alone.')


# load recipe selection help text
def load_recipe_help_text():
    with open('recipe_options.txt') as f:
        return f.read()

# load recipe visualization help text
def load_visualization_help_text():
    with open('visualization_options.txt') as f:
        return f.read()

#plotting functions

def piechart(recipe_info):

    for recipe in recipe_info:
        fat = recipe[3]
        carbs = recipe[4]
        protein = recipe[5]

    print("")
    labels = ['Protein','Carbs', 'Fat']
    values = [protein*4,carbs*4, fat*9] # convert from grams to calories 
    fig = go.Figure(go.Pie(labels=labels,
        values=values,
        text = [str(protein)+"g", str(carbs)+"g", str(fat)+"g"],
        hovertemplate = "%{label} <br># of Grams: %{text}"))
    print("Launching pie chart...")
    fig.update_layout(title = "Macronutrient Breakdown by Calories")
    fig.show()

def bargraphs(recipe_info, recipe2_info):

    macros = ['Protein','Carbs', 'Fat']
    fig1 = go.Figure(data = [
        go.Bar(name = recipe_info[0][0], x = macros, y = [recipe_info[0][5], recipe_info[0][4], recipe_info[0][3]]),
        go.Bar(name = recipe2_info[0][0], x = macros, y = [recipe2_info[0][5], recipe2_info[0][4], recipe2_info[0][3]]),
    ])

    cals = ['Calories']
    fig2 = go.Figure(data = [
        go.Bar(name = recipe_info[0][0], x = cals, y = [recipe_info[0][2]]),
        go.Bar(name = recipe2_info[0][0], x = cals, y = [recipe2_info[0][2]])
    ])

    micros = ['Cholesterol', 'Sodium']
    fig3 = go.Figure(data = [
        go.Bar(name = recipe_info[0][0], x = micros, y = [recipe_info[0][6], recipe_info[0][7]]),
        go.Bar(name = recipe2_info[0][0], x = micros, y = [recipe2_info[0][6], recipe2_info[0][7]])
    ])


    fig1.update_layout(barmode = 'group', title = 'Macronutrients', yaxis = dict(title = 'Grams'))
    fig2.update_layout(barmode = 'group', title = 'Calories', yaxis = dict(title = 'Number of Calories'))
    fig3.update_layout(barmode = 'group', title = 'Cholesterol & Sodium', yaxis = dict(title = 'Milligrams'))
    print("Launching bar graphs...")
    fig1.show()
    fig2.show()
    fig3.show()

if __name__ == "__main__":

    conn = sqlite3.connect(DBNAME)
    cur = conn.cursor()

    # have the user select a recipe
    print(load_recipe_help_text())
    user_input = input("Enter one of the commands above (or 'exit' to quit the program): ")
    recipe_info = None
    while user_input != "exit":
        while recipe_info == None:
            if user_input.startswith(("search", "allrecipes", "retrieve", "random", "exit")) == False:
                user_input = input("Command Not Recognized. Please enter a valid command: ")

            if user_input.startswith("search"):
                print("")
                search_term = user_input.split(" ")[1]
                combine_recipe_info(search_term)
                insert_stuff()

                category = (search_term, )
                statement = '''
                SELECT Title 
                FROM Recipe as r
                JOIN Category as c
                on r.CategoryId = c.Id
                WHERE c.Name = ?
                '''
                cur.execute(statement, category)
                results = cur.fetchall()
                if len(results) == 0:
                    print("I'm sorry, no results were returned for category: " + search_term)
                    user_input = input("Please enter a new command: ")
                else:
                    count = 1
                    recipe_num_dict = {}
                    for recipe in results:
                        recipe_num_dict[count] = recipe[0]
                        print(str(count) + ". " + recipe[0])
                        count += 1
                    print("")
                    recipe_num = input("Pick a recipe by entering the corresponding number: ")
                    print("")
                    print("Recipe selected: " + recipe_num_dict[int(recipe_num)])
                    recipe_title = (recipe_num_dict[int(recipe_num)], )

                    statement = '''
                    SELECT r.Title, c.Name, r.Calories, r.Fat, r.Carbohydrates, r.Protein, r.Cholesterol, r.Sodium, r.URL
                    FROM Recipe as r
                    JOIN Category as c
                    ON r.CategoryId = c.Id
                    WHERE r.Title = ?
                    '''
                    cur.execute(statement, recipe_title)
                    recipe_info = cur.fetchall()


            elif user_input.startswith("allrecipes"):
                url = user_input.split(" ")[1]
                try:
                    scrape_recipe_website(url)
                    insert_stuff()

                    recipe_url = (url, )
                    statement = '''
                    SELECT r.Title, c.Name, r.Calories, r.Fat, r.Carbohydrates, r.Protein, r.Cholesterol, r.Sodium, r.URL
                    FROM Recipe as r
                    JOIN Category as c
                    ON r.CategoryId = c.Id
                    WHERE r.url = ?
                    '''
                    cur.execute(statement, recipe_url)
                    recipe_info = cur.fetchall()
                except:
                    user_input = input("Invalid url entered. Please enter a new command: ")

            elif user_input == "retrieve":
                statement = '''
                SELECT r.Title
                FROM Recipe as r
                '''
                cur.execute(statement)
                results = cur.fetchall()

                count = 1
                recipe_num_dict = {}
                for recipe in results:
                    recipe_num_dict[count] = recipe[0]
                    print(str(count) + ". " + recipe[0])
                    count += 1
                print("")
                recipe_num = input("Pick a recipe by entering the corresponding number: ")
                print("")
                print("Recipe selected: " + recipe_num_dict[int(recipe_num)])
                recipe_title = (recipe_num_dict[int(recipe_num)], )

                statement = '''
                SELECT r.Title, c.Name, r.Calories, r.Fat, r.Carbohydrates, r.Protein, r.Cholesterol, r.Sodium, r.URL
                FROM Recipe as r
                JOIN Category as c
                ON r.CategoryId = c.Id
                WHERE r.Title = ?
                '''
                cur.execute(statement, recipe_title)
                recipe_info = cur.fetchall()
    

            if user_input == "random":

                # find out the number of recipes in the database
                statement = '''
                SELECT COUNT(*)
                FROM Recipe
                '''
                cur.execute(statement)
                for row in cur:
                    num_recipes = row[0]
                
                random_num = (random.randrange(1, num_recipes),)

                statement = '''
                SELECT r.Title, c.Name, r.Calories, r.Fat, r.Carbohydrates, r.Protein, r.Cholesterol, r.Sodium, r.URL
                FROM Recipe as r
                JOIN Category as c
                ON r.CategoryId = c.Id
                WHERE r.Id = ?
                '''
                cur.execute(statement, random_num)
                recipe_info = cur.fetchall()

                for row in recipe_info:
                    recipe_title = row[0]
                print("")
                print("Recipe selected: " + recipe_title)
        
        # once a recipe has been selected, move on to visualization options
        print(load_visualization_help_text())
        user_input = input("Enter one of the commands above (or 'exit' to quit the program): ")

        if user_input not in ("file", "web", "pie chart", "compare", "exit"):
            user_input = input('Command Not Recognized. Please enter a valid command (or "help" to see options): ')

        if user_input == "file":
            df = pd.DataFrame(recipe_info)
            print("")
            print("Writing results to recipe_info.txt...")
            print("")
            print(tabulate(df, showindex=False, headers = ["Title", "Category", "Calories", "Fat", "Carbohydrates", "Protein", 
                "Cholesterol", "Sodium", "URL"]))
            print("")
            f = open("recipe_info.txt", "w")
            f.write(tabulate(df, showindex=False, headers = ["Title", "Category", "Calories", "Fat", "Carbohydrates", "Protein", 
                "Cholesterol", "Sodium", "URL"]))
            f.close()
            break
    
        elif user_input == "web":
            print("")
            print("Launching recipe in web browser...")
            for recipe in recipe_info:
                url = recipe[8]
            webbrowser.open(url)
            break

        elif user_input == "pie chart":
            piechart(recipe_info)
            break

        elif user_input == "compare":
                
            # print recipes from the database for the user to choose from
            statement = '''
            SELECT r.Id, r.Title
            FROM Recipe as r
            '''
            cur.execute(statement)
            all_recipes = cur.fetchall()
            recipe_num_dict = {}
            print("")
            print("Available Recipes to compare to: ")
            count = 1
            for recipe in all_recipes:
                recipe_num_dict[count] = recipe[1]
                print(str(recipe[0]) + ". " + recipe[1])
            print("")

            # have user select a recipe to compare to
            recipe2 = input("Pick a recipe to compare to the current recipe by entering the corresponding number: ")
            recipe2_id = (int(recipe2), )
            statement = '''
            SELECT r.Title, c.Name, r.Calories, r.Fat, r.Carbohydrates, r.Protein, r.Cholesterol, r.Sodium, r.URL
            FROM Recipe as r
            JOIN Category as c
            ON r.CategoryId = c.Id
            WHERE r.Id = ?
            '''
            cur.execute(statement, recipe2_id)
            recipe2_info = cur.fetchall()
            
            bargraphs(recipe_info, recipe2_info)
            break

    
    print("")
    print("Bye! Thanks for using my program :)")

    conn.commit()
    conn.close()

