import openai
import json
from typing import List, Dict, Any
from app.core.config_settings import Settings

class LLM:
    """Class to handle interactions with Large Language Models"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.provider = settings.LLM_PROVIDER
        self.model = settings.LLM_MODEL
        
        if self.provider == "openai":
            openai.api_key = settings.OPENAI_API_KEY
    
    def generate_response(self, prompt: str, system_prompt: str = None) -> str:
        """Generate a response from the LLM"""
        if self.provider == "openai":
            messages = []
            
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
                
            messages.append({"role": "user", "content": prompt})
            
            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages
            )

            
            return response.choices[0].message.content
        
        # Add support for other models as needed
        return "I couldn't generate a response at this time."
    
    def detect_preferences(self, message: str) -> dict:
        """Detect user preferences mentioned in a message"""
        system_prompt = """
        You are a helpful assistant that can extract user preferences about cocktails and ingredients. 
        Your task is to identify and extract mentions of favorite ingredients and favorite cocktails from the message. 
        Respond with a JSON object containing two lists: 
        "favorite_ingredients" and "favorite_cocktails". 
        If none are mentioned or words as "love", "like" etc. did not use return empty lists 
        Ensure that the output is a valid JSON object and not a plain text response.
        """
        
        prompt = f"""
        Extract the following information from the user's message only if he uses words like love, like and etc:

        Message: "{message}"

        Return a JSON object with the following format:
        {{
            "favorite_ingredients": ["ingredient1", "ingredient2"],
            "favorite_cocktails": ["cocktail1", "cocktail2"]
        }}

        If no preferences are mentioned, return empty lists. Example:
        {{
            "favorite_ingredients": [],
            "favorite_cocktails": []
        }}
        """

        try:
            # Generate the response from the LLM
            response = self.generate_response(prompt, system_prompt)
            
            # Debugging step to check the response
            print(f"Response: {response}")

            # Check if the response is non-empty and seems to be JSON-like
            if not response:
                print("Received an empty response.")
                return {"favorite_ingredients": [], "favorite_cocktails": []}

            # Try to parse the response as JSON
            try:
                result = json.loads(response)
                print("result is",result)
                return result
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON: {e}")
                return {"favorite_ingredients": [], "favorite_cocktails": []}

        except Exception as e:
            print(f"Error detecting preferences: {e}")
            return {"favorite_ingredients": [], "favorite_cocktails": []}
