import pandas as pd
from typing import List, Dict, Any
import os
from app.core.vector_db import VectorDB
from app.core.config_settings import Settings

class CocktailService:
    """Service to manage cocktail data and operations"""
    
    def __init__(self, vector_db: VectorDB):
        self.vector_db = vector_db
        self.cocktails = []
        self.df = None
        self.settings = Settings()
        self.load_data()
    
    def load_data(self):
        """Load cocktail data from CSV"""
        try:
            # Check if the data file exists
            if not os.path.exists(self.settings.COCKTAIL_DATA_PATH):
                print(f"Cocktail data file not found at {self.settings.COCKTAIL_DATA_PATH}")
                return
            
            # Load the CSV file
            self.df = pd.read_csv(self.settings.COCKTAIL_DATA_PATH)
            
            # Process the data
            processed_cocktails = []
            for _, row in self.df.iterrows():
                # Extract ingredients
                ingredients = []
                for i in range(1, 16):  # Assuming up to 15 ingredients
                    ing_col = f'strIngredient{i}'
                    measure_col = f'strMeasure{i}'
                    
                    if ing_col in row and pd.notna(row[ing_col]) and row[ing_col] != '':
                        ingredient = row[ing_col]
                        
                        # Add measurement if available
                        if measure_col in row and pd.notna(row[measure_col]) and row[measure_col] != '':
                            ingredient = f"{row[measure_col]} {ingredient}"
                        
                        ingredients.append(ingredient)
                
                # Create cocktail object
                cocktail = {
                    'id': str(row['id']),  
                    'name': row['name'],  
                    'is_alcoholic': row.get('alcoholic', '') == 'Alcoholic',  
                    'ingredients': ingredients,
                    'instructions': row.get('instructions', ''),  
                    'glass': row.get('glassType', ''),  
                    'category': row.get('category', '') 
                }
                processed_cocktails.append(cocktail)
            
            self.cocktails = processed_cocktails
            
            # Create vector index for cocktails
            self.vector_db.create_cocktail_index(processed_cocktails)
            print(f"Loaded {len(processed_cocktails)} cocktails")
            
        except Exception as e:
            print(f"Error loading cocktail data: {e}")
    
    def search_cocktails(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search for cocktails based on a text query"""
        return self.vector_db.search_similar_cocktails(query, limit)
    
    def find_cocktails_with_ingredient(self, ingredient: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Find cocktails containing a specific ingredient"""
        matching_cocktails = []
        
        ingredient_lower = ingredient.lower()
        for cocktail in self.cocktails:
            for cocktail_ingredient in cocktail['ingredients']:
                if ingredient_lower in cocktail_ingredient.lower():
                    matching_cocktails.append(cocktail)
                    break
                    
            if len(matching_cocktails) >= limit:
                break
                
        return matching_cocktails[:limit]
    
    def find_non_alcoholic_cocktails(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Find non-alcoholic cocktails"""
        non_alcoholic = [c for c in self.cocktails if not c['is_alcoholic']]
        return non_alcoholic[:limit]
    
    def find_similar_cocktails(self, cocktail_name: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Find cocktails similar to a named cocktail"""
        return self.vector_db.search_similar_cocktails_by_name(cocktail_name, limit)
    
    def recommend_cocktails_from_ingredients(self, ingredients: List[str], limit: int = 5) -> List[Dict[str, Any]]:
        """Recommend cocktails based on a list of ingredients"""
        # Create a query from the ingredients
        query = " ".join(ingredients)
        return self.vector_db.search_similar_cocktails(query, limit)