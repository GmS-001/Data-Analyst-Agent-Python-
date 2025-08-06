import os
import json
from dotenv import load_dotenv
import google.generativeai as genai

# --- Configuration (same as before) ---
load_dotenv()
try:
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found. Please set it in your .env file.")
    genai.configure(api_key=api_key, transport='rest')
except ValueError as e:
    print(e)
    exit()

# --- The new "Planner" Prompt Template ---
# This is the core instruction set for our agent's brain.
PLANNER_PROMPT_TEMPLATE = """
You are an expert data analyst agent. Your goal is to create a step-by-step plan to answer a user's request.
You have access to these tools: `web_scraper`, `python_interpreter`.
Create a JSON array of steps. Each step must be a JSON object with "step" (integer), "tool" (string), and "args" (object) keys.

---
IMPORTANT RULES FOR YOUR RESPONSE:
1. The `python_interpreter`'s "code" argument MUST be a raw python string.
2. The python code you write should ONLY manipulate a pandas DataFrame named `df`.
3. The python code has access to two pre-loaded variables:
   - `html_content`: A string containing the full HTML from the `web_scraper` tool.
   - `df`: The pandas DataFrame, which is empty initially.
4. The first python step after scraping MUST create the dataframe using the `html_content` variable, like this: `df = pd.read_html(io.StringIO(html_content))[0]`
---
User Request: {user_request}
"""

def create_analysis_plan(user_request: str):
    """
    Takes a user's request and asks the LLM to generate a step-by-step JSON plan.
    """
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    # Format the prompt with the user's actual request
    prompt = PLANNER_PROMPT_TEMPLATE.format(user_request=user_request)

    print("--- 🧠 Generating plan with Gemini... ---")
    response = model.generate_content(prompt)

    try:
        if not response.parts:
            print("\n--- ERROR: The response from the LLM was empty or blocked. ---")
            print(f"Prompt Feedback: {response.prompt_feedback}")
            return None
    except ValueError:
        pass
    
    raw_text = response.text
    ascii_text = raw_text.encode('ascii', 'ignore').decode('utf-8')

    cleaned_json_string = ascii_text.strip().replace("```json", "").replace("```", "").strip()
    
    print("\n--- Received Plan from LLM ---")
    print(cleaned_json_string)
    print("\n--- DEBUG: True String Representation for Parser ---")
    print(repr(cleaned_json_string))
    print("-------------------------------------------------\n")

    try:
        plan = json.loads(cleaned_json_string)
        return plan
    except json.JSONDecodeError:
        print(f"\n--- ERROR: JSONDecodeError: {e} ---")
        return None

def get_gemini_response(prompt: str):
    """Sends a prompt to the Gemini API and returns the text response."""
    model = genai.GenerativeModel('gemini-1.5-flash')
    print("  -> Model initialized. Calling API now...")
    response = model.generate_content(prompt)
    return response.text


DEBUGGER_PROMPT_TEMPLATE = """
You are an expert Python debugging assistant. Your task is to fix a broken piece of Python code.
You will be given the original user request, the code that failed, and the error message that it produced.
Your goal is to return only the corrected, raw Python code. Do not add any explanations, apologies, or markdown formatting.
Original User Request:
---
{user_request}
---
Failed Code:
---
{failed_code}
---
Error Message:
---
{error_message}
---
Corrected Python Code:
"""

def get_corrected_code(user_request: str, failed_code: str, error_message: str) -> str:
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = DEBUGGER_PROMPT_TEMPLATE.format(
        user_request=user_request,
        failed_code=failed_code,
        error_message=error_message
    )

    print("--- 🧠 Sending code to debugger prompt ---")
    response = model.generate_content(prompt)
    corrected_code = response.text.strip().replace("```python", "").replace("```", "").strip()
    
    return corrected_code