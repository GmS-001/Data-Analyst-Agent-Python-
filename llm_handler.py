import os
import json
import json5
import re
from dotenv import load_dotenv
from prompts import PLANNER_PROMPT_TEMPLATE, DEBUGGER_PROMPT_TEMPLATE,DATAFRAME_CREATION_PROMPT_TEMPLATE
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
                continue

            cleaned_json_string = response.text.strip().replace("```json", "").replace("```", "").strip()
            if not cleaned_json_string:
                print(f"\n--- WARNING: Cleaned string was empty on attempt {attempt + 1}. Retrying... ---")
                continue

            # ⬇️ JSON5 parsing instead of json.loads + manual escaping
            plan = json5.loads(cleaned_json_string)

            print(f"\n--- Received Final Plan from LLM ---\n{cleaned_json_string}")
            return plan  # Success!

        except Exception as e:
            print(f"\n--- WARNING: Attempt {attempt + 1} failed to get a valid final plan. Error: {e}. Retrying... ---")
            if attempt == 2:
                print("\n--- ERROR: Max retries reached. Could not get a valid final plan. ---")
                return None



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
    ans = response.text.strip().replace("```python", "").replace("```", "").strip()
    #print("Ans from debugger: ",ans)
    return ans

