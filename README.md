# Cocktail Advisor Chat

A Python-based chat application that integrates with a large language model (LLM) to create a Retrieval-Augmented Generation (RAG) system for cocktail recommendations.

## Features

- **Chat Interface**: Simple and intuitive web-based chat interface
- **LLM Integration**: Uses OpenAI's API to handle natural language queries
- **Vector Database**: FAISS integration for efficient similarity search
- **User Memory**: Tracks user preferences for personalized recommendations
- **RAG System**: Enhances LLM responses with cocktail dataset information

## Requirements

- Python 3.8+
- FastAPI
- FAISS vector database
- Sentence Transformers
- OpenAI API key (or other LLM provider)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/poladibrahim/RAG_chatbot.git
cd RAG_chatbot
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Download the cocktail dataset from Kaggle:
   - https://www.kaggle.com/datasets/aadyasingh55/cocktails
   - Save it to `data/cocktails_original.csv`

5. Preprocess the dataset:
```bash
python scripts/preprocess_data.py --input data/cocktails_original.csv --output data/cocktails.csv
```

6. Create a `.env` file with your configuration:
```
OPENAI_API_KEY=your_openai_api_key
LLM_PROVIDER=openai
LLM_MODEL=gpt-3.5-turbo
VECTOR_DB_TYPE=faiss
VECTOR_DB_PATH=data/vector_db
COCKTAIL_DATA_PATH=data/cocktails.csv
```

## Running the Application

Start the FastAPI server:
```bash
python -m app.main
```

Example screenshot:

![WhatsApp Image 2025-03-04 at 11 43 07](https://github.com/user-attachments/assets/128da8cc-da8f-4a4f-8d85-120edac9d4dd)



The application will be available at `http://localhost:8000`

## Project Structure

```
cocktail-advisor/
├── app/
│   ├── api/             
│   │   ├── chat.py
│   │   ├── memory.py
│   ├── core/  
│   │   ├── config_settings.py
│   │   ├── llm.py
│   │   ├── vector_db.py
│   ├── models/          
│   │   ├── schemas.py
│   ├── services/        
│   │   ├── cocktail.py
│   │   ├── memory.py
│   │   ├── rag.py
│   ├── static/         
│   │   ├── script.js
│   │   ├── style.css
│   ├── templates/
│   │   ├── index.html
│   └── main.py
├── data/
│   ├── vector_db/
│   ├── cocktails.csv
├── scripts/
│   ├── preprocess_Data.py








