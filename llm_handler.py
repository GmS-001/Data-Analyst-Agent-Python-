import os
import json
from dotenv import load_dotenv
from prompts import PLANNER_PROMPT_TEMPLATE, DEBUGGER_PROMPT_TEMPLATE,CLEANER_PROMPT_TEMPLATE,DATAFRAME_CREATION_PROMPT_TEMPLATE
import google.generativeai as genai

load_dotenv()
try:
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found. Please set it in your .env file.")
    genai.configure(api_key=api_key, transport='rest')
except ValueError as e:
    print(e)
    exit()


def create_dynamic_plan(user_request: str, df_preview: dict):
    model = genai.GenerativeModel('gemini-1.5-flash')
    prompt = PLANNER_PROMPT_TEMPLATE.format(
        user_request=user_request,
        df_columns=df_preview['columns'],
        df_head=df_preview['head']
    )
    print("--- 🧠 Asking AI for the final, data-aware plan... ---")
    for attempt in range(3):
        try:
            response = model.generate_content(prompt)
            if not response.parts:
                print(f"\n--- WARNING: Response was empty or blocked on attempt {attempt + 1}. Feedback: {response.prompt_feedback}. Retrying... ---")
                continue # Skip to the next attempt
            cleaned_json_string = response.text.strip().replace("```json", "").replace("```", "").strip()
            if not cleaned_json_string:
                 print(f"\n--- WARNING: Cleaned string was empty on attempt {attempt + 1}. Retrying... ---")
                 continue
            plan = json.loads(cleaned_json_string)
            print(f"\n--- Received Final Plan from LLM ---\n{cleaned_json_string}")
            return plan # Success!

        except (json.JSONDecodeError, Exception) as e:
            print(f"\n--- WARNING: Attempt {attempt + 1} failed to get a valid final plan. Error: {e}. Retrying... ---")
            if attempt == 2:
                print("\n--- ERROR: Max retries reached. Could not get a valid final plan. ---")
                return None
            
def create_analysis_plan(user_request: str):
    """Generates a plan and retries on JSON failure."""
    model = genai.GenerativeModel('gemini-1.5-flash')
    prompt = PLANNER_PROMPT_TEMPLATE.format(user_request=user_request)
    print("--- 🧠 Generating plan with Gemini... ---")
    for attempt in range(3):
        try:
            response = model.generate_content(prompt)
            cleaned_json_string = response.text.strip().replace("```json", "").replace("```", "").strip()
            plan = json.loads(cleaned_json_string)
            print(f"\n--- Received Plan from LLM ---\n{cleaned_json_string}")
            return plan
        except (json.JSONDecodeError, Exception) as e:
            print(f"\n--- WARNING: Attempt {attempt + 1} failed to get a valid plan. Error: {e}. Retrying... ---")
            if attempt == 2: return None


def get_dataframe_creation_code(user_request: str, html_content: str) -> str:
    model = genai.GenerativeModel('gemini-1.5-flash')
    truncated_html = html_content[:50000]

    prompt = DATAFRAME_CREATION_PROMPT_TEMPLATE.format(
        user_request=user_request,
        html_content=truncated_html
    )
    print("--- 🧠 Asking for DataFrame creation script... ---")
    response = model.generate_content(prompt)
    return response.text.strip().replace("```python", "").replace("```", "").strip()


def get_gemini_response(prompt: str):
    """Sends a prompt to the Gemini API and returns the text response."""
    model = genai.GenerativeModel('gemini-1.5-flash')
    print("  -> Model initialized. Calling API now...")
    response = model.generate_content(prompt)
    return response.text



def get_corrected_code(user_request: str, full_plan: str, failed_step_number: int, failed_code: str, error_history: str) -> str:
    model = genai.GenerativeModel('gemini-1.5-flash')
    prompt = DEBUGGER_PROMPT_TEMPLATE.format(
        user_request=user_request,
        full_plan=full_plan,
        failed_step_number=failed_step_number,
        failed_code=failed_code,
        error_history=error_history
    )
    print("--- 🧠 Sending code to smart debugger... ---")
    response = model.generate_content(prompt)
    return response.text.strip().replace("```python", "").replace("```", "").strip()



def get_cleaning_code(user_request: str, df_columns: list, df_head: str) -> str:
    """Generates the specific Python code for cleaning the dataframe."""
    model = genai.GenerativeModel('gemini-1.5-flash')
    prompt = CLEANER_PROMPT_TEMPLATE.format(
        user_request=user_request,
        df_columns=df_columns,
        df_head=df_head
    )
    print("--- 🧠 Asking AI for a specific Code to clean dataframe... ---")
    response = model.generate_content(prompt)
    return response.text.strip().replace("```python", "").replace("```", "").strip()