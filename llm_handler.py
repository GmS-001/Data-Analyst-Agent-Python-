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
You have access to the following tools:
1.  `web_scraper`: Use this to get data from a specific URL. The tool needs a "url".
2.  `python_interpreter`: Use this to execute Python code for data analysis and manipulation (using pandas). The tool needs the "code". The data is available in a pandas DataFrame called `df`.
3.  `plot_generator`: Use this to create plots from the data. The tool needs the "code" to generate the plot (e.g., `df.plot(...)`).

Based on the user's request, create a JSON array of steps. Each step must be a JSON object with three keys: "step" (an integer), "tool" (the name of the tool to use), and "args" (a dictionary of arguments for the tool, like "url" or "code").

---
IMPORTANT RULES FOR YOUR RESPONSE:
1. The value for any "code" argument MUST be a valid, single-line JSON string. This means all newline characters inside the code must be escaped as `\\n`, and all double quotes must be escaped as `\\"`.
2. The value for the "code" argument MUST contain ONLY the raw Python code to be executed. DO NOT wrap it in another JSON object.
---

User Request:
---
{user_request}
---
"""

def create_analysis_plan(user_request: str):
    """
    Takes a user's request and asks the LLM to generate a step-by-step JSON plan.
    """
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    # Format the prompt with the user's actual request
    prompt = PLANNER_PROMPT_TEMPLATE.format(user_request=user_request)

    print("--- Sending Planner Prompt to LLM ---")
    print(prompt) # Good for debugging to see the final prompt
    
    response = model.generate_content(prompt)
    
    # The LLM might return the JSON inside a markdown code block, so we clean it up.
    # "```json\n{...}\n```" -> "{...}"
    cleaned_json_string = response.text.strip().replace("```json", "").replace("```", "").strip()
    
    print("\n--- Received Plan from LLM ---")
    print(cleaned_json_string)

    try:
        # Parse the cleaned string into a Python list of dictionaries
        plan = json.loads(cleaned_json_string)
        return plan
    except json.JSONDecodeError:
        print("\n--- ERROR: LLM did not return valid JSON. ---")
        return None

# Function to get a response from the Gemini model
def get_gemini_response(prompt: str):
    """Sends a prompt to the Gemini API and returns the text response."""
    # We are using the 'gemini-1.5-flash' model, which is fast and cost-effective.
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
    """
    Asks the LLM to debug a piece of failed code.
    """
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = DEBUGGER_PROMPT_TEMPLATE.format(
        user_request=user_request,
        failed_code=failed_code,
        error_message=error_message
    )

    print("--- 🧠 Sending code to debugger prompt ---")
    response = model.generate_content(prompt)
    
    # Clean up the response to get only the raw code
    corrected_code = response.text.strip().replace("```python", "").replace("```", "").strip()
    
    return corrected_code