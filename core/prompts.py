from langchain.prompts import PromptTemplate

prompts = {
    "story_to_plan": PromptTemplate.from_template("""
You are a QA automation assistant.
Your task is to convert a given user story into a clear sequence of UI actions.

Example:
User Story: "As a user, I want to log in to my account."
Output Plan:
1. Navigate to login page
2. Enter username
3. Enter password
4. Click login button

Now process this:
User Story: {user_story}
Output Plan:
"""),
    "plan_to_code": PromptTemplate.from_template("""
You are a QA automation engineer.
Convert the following test plan into executable Playwright Python code.

Test Plan:
{plan}

Use best practices:
- Use async/await
- Use page.locator()
- Add waits where necessary

Return only the code, no explanation.
""")
}