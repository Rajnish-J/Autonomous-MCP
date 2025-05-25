# from langchain_openai import AzureChatOpenAI

# azure_openai = AzureChatOpenAI(
#     azure_deployment="gpt-4o",
#     temperature=0,
#     azure_endpoint="https://your-endpoint.openai.azure.com/ ",
#     api_key="YOUR_API_KEY",
#     api_version="2025-01-01-preview"
# )

import google.generativeai as genai
import os

API_KEY = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=API_KEY)

gemini_model = genai.GenerativeModel("gemini-2.0-flash-exp")

response = gemini_model.generate_content("Write a short story about a robot learning to paint.")
print(response.text)