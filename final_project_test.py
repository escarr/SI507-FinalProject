import unittest
from final_project import *

class TestDatabase(unittest.TestCase):
    def test_recipe_table(self):
        conn = sqlite3.connect(DBNAME)
        cur = conn.cursor()

        # check to make sure column names are correct
        statement = '''
        PRAGMA table_info("Recipe")
        '''
        cur.execute(statement)
        results = cur.fetchall()
        col_names = []
        for row in results:
            col_names.append(row[1])

        self.assertEqual(len(col_names), 10)
        self.assertEqual(col_names, ["Id", "Title", "Calories", "Fat", "Carbohydrates", 
            "Protein", "Cholesterol", "Sodium", "URL", "CategoryId"])

        # check to make sure the table was correctly pre-populated with recipes
        statement = '''
        SELECT Title
        FROM Recipe
        '''
        cur.execute(statement)
        results = cur.fetchall()
        self.assertIn(('Classic Savory Deviled Eggs', ), results)
 
        conn.close()

    def test_category_table(self):
        conn = sqlite3.connect(DBNAME)
        cur = conn.cursor()

        # check to make sure column names are correct
        statement = '''
        PRAGMA table_info("Category")
        '''
        cur.execute(statement)
        results = cur.fetchall()
        col_names = []
        for row in results:
            col_names.append(row[1])

        self.assertEqual(len(col_names), 2)
        self.assertEqual(col_names, ["Id", "Name"])

        # check to make sure the table was correctly pre-populated with recipes
        statement = '''
        SELECT Name
        FROM Category
        '''
        cur.execute(statement)
        results = cur.fetchall()
        self.assertIn(('burger',), results)
        self.assertIn(('Appetizers and Snacks',), results)

        conn.close()

    def test_joins(self):
        conn = sqlite3.connect(DBNAME)
        cur = conn.cursor()

        statement = '''
        SELECT c.Name
        FROM Recipe as r
        JOIN Category as c
        on r.CategoryId = c.Id
        '''
        cur.execute(statement)
        results = cur.fetchall()
        self.assertIn(('burger',), results)
        self.assertIn(('Appetizers and Snacks',), results)

        conn.close()

class TestDataSources(unittest.TestCase):
    
    def test_spoonacular(self):
        conn = sqlite3.connect(DBNAME)
        cur = conn.cursor()
        #search for new term
        combine_recipe_info("pizza")
        insert_stuff()
        statement = '''
        SELECT r.Title
        FROM Recipe as r
        JOIN Category as c
        ON r.CategoryId = c.Id
        WHERE c.Name = "pizza"
        '''
        cur.execute(statement)
        results = cur.fetchall()
        self.assertEqual(len(results), 10)

        statement = '''
        SELECT Name
        FROM Category
        '''
        cur.execute(statement)
        results = cur.fetchall()
        self.assertIn(('pizza', ), results)

        conn.close()


    def test_allrecipes(self):
        conn = sqlite3.connect(DBNAME)
        cur = conn.cursor()
        #enter url
        scrape_recipe_website("https://www.allrecipes.com/recipe/228331/gingerbread-cake-vegan-and-gluten-free/?internalSource=hub%20recipe&referringContentType=Search&clickId=cardslot%204")
        insert_stuff()
        statement = '''
        SELECT r.Title, r.Calories, c.Name
        FROM Recipe as r
        JOIN Category as c
        ON r.CategoryId = c.Id
        WHERE Title = "Gingerbread Cake - Vegan and Gluten-Free"
        '''
        cur.execute(statement)
        results = cur.fetchall()
        self.assertEqual(results[0][0], "Gingerbread Cake - Vegan and Gluten-Free")
        self.assertEqual(results[0][1], 166)
        self.assertEqual(results[0][2], "Cakes")

        conn.close()

class TestPlotting(unittest.TestCase):

    def test_pie_chart(self):
        conn = sqlite3.connect(DBNAME)
        cur = conn.cursor()
        statement = '''
            SELECT r.Title, c.Name, r.Calories, r.Fat, r.Carbohydrates, r.Protein, r.Cholesterol, r.Sodium, r.URL
            FROM Recipe as r
            JOIN Category as c
            ON r.CategoryId = c.Id
            LIMIT 1
            '''
        cur.execute(statement)
        recipe_info = cur.fetchall()
        try:
            piechart(recipe_info)
        except:
            self.fail()

        conn.close()
    
    def test_bar_graph(self):
        conn = sqlite3.connect(DBNAME)
        cur = conn.cursor()
        statement = '''
            SELECT r.Title, c.Name, r.Calories, r.Fat, r.Carbohydrates, r.Protein, r.Cholesterol, r.Sodium, r.URL
            FROM Recipe as r
            JOIN Category as c
            ON r.CategoryId = c.Id
            LIMIT 2
            '''
        cur.execute(statement)
        recipes = cur.fetchall()
        recipe1_info = recipes[0]
        recipe2_info = recipes[1]
        try:
            bargraphs(recipe1_info, recipe2_info)
        except:
            self.fail()

        conn.close()

unittest.main()
