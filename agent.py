# agent.py
import pandas as pd
import requests
from llm_handler import create_analysis_plan, get_corrected_code
from tools import web_scraper, python_interpreter

AVAILABLE_TOOLS = { "web_scraper": web_scraper, "python_interpreter": python_interpreter }
MAX_RETRIES = 2 # Set the maximum number of times the agent can try to fix its code


def execute_plan(user_request: str, plan: list):
    """Executes a plan, handling errors and using a self-correction loop."""
    data_context = {"df": pd.DataFrame()}

    for step in sorted(plan, key=lambda x: x['step']):
        tool_name = step['tool']
        args = step['args']
        print(f"\n---  Executing Step {step['step']}: {tool_name} ---")

        if tool_name not in AVAILABLE_TOOLS:
            print(f"--- ⚠️ Error: Tool '{tool_name}' not found. ---")
            data_context['error'] = f"Tool '{tool_name}' not found."
            break
        
        current_code = args.get("code")
        
        for attempt in range(MAX_RETRIES):
            # Pass the current code to the tool
            args["code"] = current_code
            result_context = AVAILABLE_TOOLS[tool_name](**args, data_context=data_context)
            
            if result_context.get('status') == 'success':
                # If successful, update context and move to the next step
                data_context.update(result_context)
                break # Exit the retry loop
            else:
                # If it fails, enter the self-correction loop
                error_message = result_context.get('error_message', 'An unknown error occurred.')
                print(f"--- 🔁 Attempt {attempt + 1} failed. Asking LLM to debug... ---")
                
                # Get corrected code from the debugger
                corrected_code = get_corrected_code(user_request, current_code, error_message)
                current_code = corrected_code # Update the code for the next attempt
                
                if attempt == MAX_RETRIES - 1:
                    print("--- 🚫 Max retries reached. Failing step. ---")
                    data_context['error'] = f"Max retries reached. Last error: {error_message}"
                    break # Exit the retry loop

        if 'error' in data_context:
            print(f"Stopping execution due to an unrecoverable error in Step {step['step']}.")
            break
            
    print("\n--- ✅ Plan Execution Finished ---")
    return data_context

if __name__ == '__main__':
    user_request = """
    Scrape the list of highest grossing films from Wikipedia. It is at the URL:
    https://en.wikipedia.org/wiki/List_of_highest-grossing_films

    Using the main table in the page, create a pandas DataFrame. The 'Worldwide gross' column should be cleaned to be a numeric type.
    Then, print the following answers:
    1. How many movies grossed over $2.5 billion?
    2. What is the average gross of movies released in 2019?
    """

    # --- NEW: Caching Logic ---
    import os
    import json
    
    plan_cache_file = "plan_cache.json"
    plan = None

    # If a cached plan exists, load it.
    if os.path.exists(plan_cache_file):
        print("--- Found cached plan. Loading from file. ---")
        with open(plan_cache_file, 'r') as f:
            plan = json.load(f)
    else:
        print("--- No cached plan found. Generating new plan from LLM. ---")
        plan = create_analysis_plan(user_request)
        if plan:
            with open(plan_cache_file, 'w') as f:
                json.dump(plan, f, indent=2)
            print(f"--- Plan saved to {plan_cache_file} for future use. ---")

    if plan:
        # The rest of the execution is the same
        final_context = execute_plan(user_request, plan)
        print("\n--- Final Results ---")
        if 'last_code_output' in final_context:
            print(f"\nFinal text output from code execution:\n{final_context['last_code_output']}")
        if 'df' in final_context and not final_context['df'].empty:
            print("\nFirst 5 rows of the final DataFrame:")
            print(final_context['df'].head())
        if 'error' in final_context:
            print(f"\nAn error occurred: {final_context['error']}")