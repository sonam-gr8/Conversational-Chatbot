from transformers import pipeline
from langdetect import detect
import gradio as gr
import re
from dotenv import load_dotenv
import os
import mysql.connector

load_dotenv()  # Load environment variables from .env

conn = mysql.connector.connect(
    host=os.getenv("DB_HOST"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    database=os.getenv("DB_NAME")
)


cursor = conn.cursor()

# Load multilingual transformer
generator = pipeline("text2text-generation", model="google/flan-t5-base")  # lightweight + multilingual

def chatbot_response(message,history):
    lang = detect(message)
    
    # Normalize input: ask model to identify the topic
    prompt = f"What are the main words in this sentence? {message}"
    subject = generator(prompt, max_length=20)[0]['generated_text'].strip().lower()
    print("Subject --- ", subject)
    subject=subject.split(",")
    for i in range(len(subject)):
        subject[i]=subject[i].strip()

    # Search for answer
    for i in subject:
        cursor.execute("SELECT info FROM knowledge WHERE topic LIKE %s", ("%" + i + "%",))
        response = cursor.fetchone()
        if response:
            break

    # If not found, fallback
    if not response:
        match = re.search(r"\b(?:chicken|beef|veg|pork)?\s*momo\b", message.lower())
        if match:
            cursor.execute("SELECT info FROM knowledge WHERE topic LIKE %s", ("%" + match.group() + "%",))
            response = cursor.fetchone()
        if not response:
            response = f"Sorry, I couldn’t find information about '{subject}'."

    return response[0]

# Gradio UI
iface = gr.ChatInterface(
    fn=chatbot_response,
    type="messages",
    theme='ocean',
    title="Kalimpong Bot",
    description="Ask in broken English, Hindi, or Hinglish. The bot will try to understand and reply "
)

iface.launch(share=True)

#finished integration with mysql, more effort on properly searching key words and increasing knowledge data base