import os
import json
from dotenv import load_dotenv
from prompts import PLANNER_PROMPT_TEMPLATE, DEBUGGER_PROMPT_TEMPLATE
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


def create_analysis_plan(user_request: str):
    model = genai.GenerativeModel('gemini-1.5-flash')
    prompt = PLANNER_PROMPT_TEMPLATE.format(user_request=user_request)
    for attempt in range(3): # Try up to 3 times
        try:
            response = model.generate_content(prompt)
            
            if not response.parts:
                print(f"\n--- ERROR: Response was empty or blocked on attempt {attempt + 1}. Feedback: {response.prompt_feedback} ---")
                continue 

            ascii_text = response.text.encode('ascii', 'ignore').decode('utf-8')
            cleaned_json_string = ascii_text.strip().replace("```json", "").replace("```", "").strip()
                    
            # Try to parse the JSON. If it succeeds, we're done.
            plan = json.loads(cleaned_json_string)
            print(f"\n--- Received Plan from LLM ---\n{cleaned_json_string}")
            return plan # Success! Exit the function.

        except json.JSONDecodeError as e:
            print(f"\n--- WARNING: Attempt {attempt + 1} failed to parse JSON. Error: {e}. Retrying... ---")
            # If we've used up all our retries, fail gracefully.
            if attempt == 2:
                print("\n--- ERROR: Max retries reached. Could not get a valid JSON plan. ---")
                return None
        except Exception as e:
            print(f"\n--- ERROR: An unexpected error occurred during plan generation: {e} ---")
            return None
    
    return None

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