import os

from langchain_google_genai import ChatGoogleGenerativeAI

"""
Triage Agent

Its core prompt should be a chain-of-thought process that walks through the ESI decision points using the symptoms, 
history, AND vital signs.
"""

model = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-preview-05-20",
    temperature=1.0,
    max_retries=1,
    google_api_key=os.getenv("GEMINI_API_KEY"),
)
