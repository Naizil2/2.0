# app.py
import os
import requests
from bs4 import BeautifulSoup
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS

# --- Helper Functions for Summarization ---

def fetch_article_content(url: str) -> str:
    """Fetches and extracts the main text content from a news article URL."""
    print(f"Fetching content from: {url}")
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # This selector targets the main content container from your generated HTML
        container = soup.find('div', class_='container')
        if not container:
            return "Error: Could not find the main news container."

        paragraphs = container.find_all('p')
        article_text = ' '.join([p.get_text() for p in paragraphs])

        if not article_text:
            return "Error: Could not find any paragraph content on the page."

        print("Successfully fetched and parsed content.")
        return article_text

    except requests.exceptions.RequestException as e:
        return f"Error: Failed to fetch URL content. {e}"
    except Exception as e:
        return f"An unexpected error occurred: {e}"

def summarize_with_gemini(api_key: str, article_text: str) -> str:
    """Summarizes the given text using the Gemini LLM via LangChain."""
    print("Initializing LLM and preparing for summarization...")
    
    prompt_template = """
    You are an expert news summarizer. Your goal is to provide a concise, easy-to-understand summary 
    of the following news article content. Focus on the key points and present them clearly.

    Article Content:
    "{article_text}"

    Your Concise Summary:
    """
    prompt = PromptTemplate(input_variables=["article_text"], template=prompt_template)
    
    llm = ChatGoogleGenerativeAI(
        model="gemini-pro",
        google_api_key=api_key,
        temperature=0.3,
        convert_system_message_to_human=True
    )
    
    chain = LLMChain(llm=llm, prompt=prompt)

    print("Generating summary...")
    summary = chain.run({"article_text": article_text})
    return summary

# --- Flask API Application ---

# Load environment variables (for GOOGLE_API_KEY)
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

# Initialize Flask app
app = Flask(__name__)
# Enable Cross-Origin Resource Sharing to allow your frontend to call the API
CORS(app) 

@app.route('/summarize', methods=['POST'])
def summarize_endpoint():
    """
    API endpoint to summarize a news article.
    Expects a JSON payload with a "url" key.
    """
    if not api_key:
        return jsonify({"error": "GOOGLE_API_KEY not found on the server."}), 500

    data = request.get_json()
    if not data or 'url' not in data:
        return jsonify({"error": "Invalid request. 'url' not provided."}), 400

    news_url = data['url']
    
    # The URL needs to be a full path. We assume the server runs from the project root.
    # The frontend will send a relative path like /News/Category/id.html
    # We need to construct the correct local file path.
    # However, it's better if the frontend sends the full URL. Let's adjust the frontend logic for that.
    
    full_url = request.host_url + news_url.lstrip('/')

    article_content = fetch_article_content(full_url)
    if "Error:" in article_content:
        return jsonify({"error": article_content}), 500

    try:
        summary = summarize_with_gemini(api_key, article_content)
        return jsonify({"summary": summary})
    except Exception as e:
        return jsonify({"error": f"Failed to generate summary. {e}"}), 500

if __name__ == '__main__':
    # Make sure to have a .env file with your GOOGLE_API_KEY
    # pip install python-dotenv langchain-google-genai Flask Flask-Cors requests beautifulsoup4
    print("Starting summarization server...")
    app.run(host='0.0.0.0', port=5000)