from typing import List, Dict, Any, Tuple
from app.core.llm import LLM
from app.core.vector_db import VectorDB
from app.services.cocktail import CocktailService
from app.services.memory import MemoryService

class RAGService:
    """Service to handle Retrieval-Augmented Generation"""
    
    def __init__(
        self, 
        llm: LLM, 
        vector_db: VectorDB, 
        cocktail_service: CocktailService,
        memory_service: MemoryService
    ):
        self.llm = llm
        self.vector_db = vector_db
        self.cocktail_service = cocktail_service
        self.memory_service = memory_service
    
    def process_message(self, message: str, session_id: str) -> Tuple[str, Dict[str, List[str]]]:
        try:
            preferences = self.llm.detect_preferences(message)
            if not preferences:
                print(f"Preferences detection failed for message: {message}")
            

            # Check if preferences are found, and update memory
            if preferences.get('favorite_ingredients') or preferences.get('favorite_cocktails'):
                self.memory_service.update_user_memory(session_id, preferences)

            # Get user memory
            user_memory = self.memory_service.get_user_memory(session_id)
            
            # Manually set default values if they do not exist
            if not user_memory.favorite_ingredients:
                user_memory.favorite_ingredients = []  # Initialize if None
            if not user_memory.favorite_cocktails:
                user_memory.favorite_cocktails = []  # Initialize if None
            user_memory_dict = {
                'favorite_ingredients': user_memory.favorite_ingredients,
                'favorite_cocktails': user_memory.favorite_cocktails
            }
            # Generate response based on user memory
            response = self._generate_contextualized_response(message, user_memory_dict)
            
            return response, preferences
        
        except Exception as e:
            print(f"Error in process_message: {e}")
            return "An error occurred while processing your message.", {}

    
    def _generate_contextualized_response(self, message: str, user_memory: Dict[str, Any]) -> str:
        """Generate a response with context from user memory and cocktail knowledge"""
        # Determine message intent
        intent = self._determine_message_intent(message)
        
        # Retrieve relevant information based on intent
        context = self._retrieve_context(message, intent, user_memory)
        
        # Generate system prompt
        system_prompt = """
        You are a helpful cocktail advisor. You provide information about cocktails, 
        ingredients, and can make recommendations based on user preferences.
        
        Be concise, friendly, and informative. If you don't know something, say so.
        
        Always respond in a conversational manner.
        """
        
        # Generate user prompt with context
        user_prompt = f"""
        User message: {message}
        
        User's favorite ingredients: {', '.join(user_memory.get('favorite_ingredients', ['None mentioned yet']))}
        User's favorite cocktails: {', '.join(user_memory.get('favorite_cocktails', ['None mentioned yet']))}
        
        Context information:
        {context}
        
        Please respond to the user's message using the context provided.
        """
        
        # Generate response
        response = self.llm.generate_response(user_prompt, system_prompt)
        print(f"Generated response: {response}") 
        if not response:
            raise ValueError("LLM returned an empty response")
        return response
    
    def _determine_message_intent(self, message: str) -> str:
        """Determine the intent of the user message"""
        message_lower = message.lower()
        
        # Check for specific intents
        if "recommend" in message_lower or "suggest" in message_lower:
            if "similar to" in message_lower or "like" in message_lower:
                return "similar_cocktail"
            if "favorite" in message_lower or "favourite" in message_lower:
                return "recommend_from_favorites"
            return "recommend"
        
        if "non-alcoholic" in message_lower or "nonalcoholic" in message_lower:
            return "non_alcoholic"
        
        if "favorite" in message_lower or "favourite" in message_lower:
            if "ingredient" in message_lower:
                return "favorite_ingredients"
            if "cocktail" in message_lower:
                return "favorite_cocktails"
                
        if "containing" in message_lower or "with" in message_lower:
            # Check if asking about cocktails with specific ingredients
            return "cocktails_with_ingredient"
        
        # Default to general query
        return "general"
    
    def _retrieve_context(self, message: str, intent: str, user_memory: Dict[str, Any]) -> str:
        """Retrieve relevant context based on intent"""
        context = ""
        
        if intent == "similar_cocktail":
            # Extract cocktail name
            # This is a simplistic approach - in a real application, use NLP for better extraction
            message_lower = message.lower()
            start_idx = message_lower.find("similar to") + 10
            if start_idx < 10:  # Not found
                start_idx = message_lower.find("like") + 5
            
            if start_idx >= 5:  # Found one of the phrases
                cocktail_name = ""
                # Extract text between quotes if present
                if '"' in message[start_idx:]:
                    quote_start = message.find('"', start_idx) + 1
                    quote_end = message.find('"', quote_start)
                    if quote_end > quote_start:
                        cocktail_name = message[quote_start:quote_end]
                # Otherwise take the rest of the text
                if not cocktail_name and "'" in message[start_idx:]:
                    quote_start = message.find("'", start_idx) + 1
                    quote_end = message.find("'", quote_start)
                    if quote_end > quote_start:
                        cocktail_name = message[quote_start:quote_end]
                # Last resort - take all text after "similar to" or "like"
                if not cocktail_name:
                    cocktail_name = message[start_idx:].strip().split()[0]
                
                # Find similar cocktails
                similar_cocktails = self.cocktail_service.find_similar_cocktails(cocktail_name, 5)
                context += f"Similar cocktails to '{cocktail_name}':\n"
                for idx, cocktail in enumerate(similar_cocktails):
                    context += f"{idx+1}. {cocktail['name']} - Ingredients: {', '.join(cocktail['ingredients'])}\n"
        
        elif intent == "recommend_from_favorites":
            # Get user's favorite ingredients
            fav_ingredients = user_memory.get('favorite_ingredients', [])
            
            if fav_ingredients:
                # Find cocktails with favorite ingredients
                recommended_cocktails = self.cocktail_service.recommend_cocktails_from_ingredients(fav_ingredients, 5)
                context += "Recommended cocktails based on your favorite ingredients:\n"
                for idx, cocktail in enumerate(recommended_cocktails):
                    context += f"{idx+1}. {cocktail['name']} - Ingredients: {', '.join(cocktail['ingredients'])}\n"
            else:
                context += "You haven't shared any favorite ingredients yet. Let me know what ingredients you enjoy!\n"
        
        elif intent == "non_alcoholic":
            # Check if message mentions specific ingredients
            ingredients_to_find = []
            message_lower = message.lower()
            common_ingredients = ["sugar", "lemon", "lime", "orange", "mint", "ginger"]
            
            for ingredient in common_ingredients:
                if ingredient in message_lower:
                    ingredients_to_find.append(ingredient)
            
            # Find non-alcoholic cocktails
            non_alcoholic = self.cocktail_service.find_non_alcoholic_cocktails(10)
            
            if ingredients_to_find:
                # Filter for those containing the mentioned ingredients
                filtered_cocktails = []
                for cocktail in non_alcoholic:
                    for ingredient in ingredients_to_find:
                        if any(ingredient.lower() in cocktail_ing.lower() for cocktail_ing in cocktail['ingredients']):
                            filtered_cocktails.append(cocktail)
                            break
                    
                    if len(filtered_cocktails) >= 5:
                        break
                
                context += f"Non-alcoholic cocktails containing {', '.join(ingredients_to_find)}:\n"
                for idx, cocktail in enumerate(filtered_cocktails[:5]):
                    context += f"{idx+1}. {cocktail['name']} - Ingredients: {', '.join(cocktail['ingredients'])}\n"
            else:
                # Just return general non-alcoholic cocktails
                context += "Non-alcoholic cocktails:\n"
                for idx, cocktail in enumerate(non_alcoholic[:5]):
                    context += f"{idx+1}. {cocktail['name']} - Ingredients: {', '.join(cocktail['ingredients'])}\n"
        
        elif intent == "favorite_ingredients":
            fav_ingredients = user_memory.get('favorite_ingredients', [])
            if fav_ingredients:
                context += f"Your favorite ingredients are: {', '.join(fav_ingredients)}\n"
            else:
                context += "You haven't shared any favorite ingredients yet.\n"
        
        elif intent == "favorite_cocktails":
            fav_cocktails = user_memory.get('favorite_cocktails', [])
            if fav_cocktails:
                context += f"Your favorite cocktails are: {', '.join(fav_cocktails)}\n"
            else:
                context += "You haven't shared any favorite cocktails yet.\n"
        
        elif intent == "cocktails_with_ingredient":
            # Extract ingredient(s) from the message
            ingredients = []
            message_lower = message.lower()
            
            # Common ingredients to check for
            common_ingredients = ["vodka", "rum", "gin", "tequila", "whiskey", "bourbon", 
                                 "lemon", "lime", "orange", "grapefruit", "sugar", "syrup",
                                 "mint", "basil", "soda", "tonic", "juice", "water", "bitters"]
            
            for ingredient in common_ingredients:
                if ingredient in message_lower:
                    ingredients.append(ingredient)
            
            # If no specific ingredients found, look for keywords
            if not ingredients:
                if "contain" in message_lower:
                    parts = message_lower.split("contain")
                    if len(parts) > 1:
                        ing_part = parts[1].strip()
                        ingredients = [ing.strip() for ing in ing_part.split(",")]
                        # Clean up any remaining text
                        if ingredients and " " in ingredients[-1]:
                            ingredients[-1] = ingredients[-1].split()[0]
                elif "with" in message_lower:
                    parts = message_lower.split("with")
                    if len(parts) > 1:
                        ing_part = parts[1].strip()
                        ingredients = [ing.strip() for ing in ing_part.split(",")]
                        # Clean up any remaining text
                        if ingredients and " " in ingredients[-1]:
                            ingredients[-1] = ingredients[-1].split()[0]
            
            if ingredients:
                for ingredient in ingredients:
                    cocktails = self.cocktail_service.find_cocktails_with_ingredient(ingredient, 5)
                    context += f"Cocktails containing {ingredient}:\n"
                    for idx, cocktail in enumerate(cocktails):
                        context += f"{idx+1}. {cocktail['name']} - Ingredients: {', '.join(cocktail['ingredients'])}\n"
            else:
                context += "I couldn't identify which ingredient you're asking about.\n"
        
        else:  # General query
            # Use vector search to find relevant cocktails
            cocktails = self.cocktail_service.search_cocktails(message, 3)
            if cocktails:
                context += "Here are some cocktails that might be relevant:\n"
                for idx, cocktail in enumerate(cocktails):
                    context += f"{idx+1}. {cocktail['name']} - Ingredients: {', '.join(cocktail['ingredients'])}\n"
            
            # Add user's preferences to context if available
            fav_ingredients = user_memory.get('favorite_ingredients', [])
            if fav_ingredients:
                context += f"\nYour favorite ingredients are: {', '.join(fav_ingredients)}\n"
            
            fav_cocktails = user_memory.get('favorite_cocktails', [])
            if fav_cocktails:
                context += f"Your favorite cocktails are: {', '.join(fav_cocktails)}\n"
        
        return context