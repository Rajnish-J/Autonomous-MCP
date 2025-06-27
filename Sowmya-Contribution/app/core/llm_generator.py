from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
import os
from dotenv import load_dotenv
load_dotenv()


api_key = os.getenv("GEMINI_API_KEY")

llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.2)

template = """Generate Playwright Python code (sync version) for this test case:

{test_case}

- Use 'headed' mode
- Do not include import statements
-Give me only valid Python code, without markdown formatting like ```.
- Ensure code is properly indented under a function called `run()`
"""

prompt = PromptTemplate(
    input_variables=["test_case"],
    template=template,
)

async def generate_test_script(test_case: str) -> str:
    formatted_prompt = prompt.format(test_case=test_case)
    response = llm.invoke(formatted_prompt)
    raw_code = response.content  
    code = clean_code(raw_code)
    print(code)
    return code

def clean_code(llm_output: str) -> str:
    # Remove triple backticks and language tags
    lines = llm_output.strip().splitlines()
    cleaned = [line for line in lines if not line.strip().startswith("```")]
    return "\n".join(cleaned)
