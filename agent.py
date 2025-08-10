# agent.py 
import pandas as pd
import json
import ast
import re
import inspect
from prompts import user_request
from llm_handler import create_analysis_plan, get_corrected_code, get_dataframe_creation_code,create_dynamic_plan
from tools import web_scraper, python_interpreter, answer_generator, data_cleaner

INITIAL_TOOLS = {
    "web_scraper": web_scraper,
    "python_interpreter": python_interpreter,
}
FINAL_EXECUTION_TOOLS = {
    "python_interpreter": python_interpreter,
    "answer_generator": answer_generator
}
MAX_RETRIES = 3

def execute_plan(user_request: str, plan: list,initial_context: dict):
    data_context = initial_context
    plan_str = json.dumps(plan, indent=2)

    for step in sorted(plan, key=lambda x: x['step']):
        tool_name = step.get('tool')
        args = step.get('args', {})
        print(f"\n--- Executing Step {step['step']}: {tool_name} ---")

        if tool_name not in FINAL_EXECUTION_TOOLS:
            data_context['error'] = f"Tool '{tool_name}' not found."
            print(f"--- ⚠️ {data_context['error']} ---")
            break
        
        if 'code' in args:
            raw_code = args['code']
            try:
                # Safely evaluate the string to see if it's a literal like a set
                code_obj = ast.literal_eval(raw_code)
                # If it's a set with one item, extract the item (the real code)
                if isinstance(code_obj, set) and len(code_obj) == 1:
                    print("---  sanitizer: Found code wrapped in a set. Extracting. ---")
                    args['code'] = list(code_obj)[0]
            except (ValueError, SyntaxError):
                # If it's not a valid literal, assume it's raw code and do nothing.
                pass
            
        tool_function = FINAL_EXECUTION_TOOLS[tool_name]
        all_possible_args = {
            "user_request": user_request,
            "data_context": data_context,
            **args
        }
        # Smartly filter for only the arguments this specific tool accepts
        tool_params = inspect.signature(tool_function).parameters
        valid_args = {name: value for name, value in all_possible_args.items() if name in tool_params}
        # --- The self-correction and execution logic ---
        current_args = valid_args
        error_history = ""
        for attempt in range(MAX_RETRIES):
            try:
                # Call the tool with only the arguments it can accept
                result_context = tool_function(**current_args)
                # If the tool doesn't return a status, assume success
                if result_context.get('status', 'success') == 'success':
                    data_context.update(result_context)
                    break # Success, exit the retry loop
                # If the tool returns an error status, trigger debugger
                else:
                    error_message = result_context.get('error_message', 'Tool returned a failure status.')
                    if attempt >= MAX_RETRIES - 1:
                        print("--- 🚫 Max retries reached. Failing step. ---")
                        data_context['error'] = f"Max retries reached. Last error: {error_message}"
                        break
                    
                    print(f"--- 🔁 Attempt {attempt + 1} failed. Asking smart debugger for a fix... ---")
                    failed_code = current_args.get("code", "N/A")
                    error_history += f"--- ATTEMPT {attempt + 1} ---\nFAILED CODE:\n{failed_code}\n\nERROR:\n{error_message}\n---\n"
                    current_args['code'] = get_corrected_code(user_request, plan_str, step['step'], error_history)

            except Exception as e:
                data_context['status'] = 'error'; data_context['error_message'] = f"Error calling tool '{tool_name}': {repr(e)}"
                break 

        if 'error' in data_context or data_context.get('status') == 'error':
            print(f"Stopping execution due to an unrecoverable error in Step {step['step']}.")
            break
            
    return data_context


def run_agent(user_request: str):
    print("--- Starting Agent ---")
    data_context = {}
    print("\n--- Phase 1: Data Gathering ---")

    # 1a. Find the URL in the user's request using a regular expression
    url_match = re.search(r"https?://\S+", user_request)
    if not url_match:
        print("--- ❌ Error: No URL found in the request. ---")
        return
    url = url_match.group(0).rstrip('.,!?;:')
    print(f"Found URL: {url}")

    # 1b. Scrape the web page
    data_context = web_scraper(url=url, data_context=data_context)
    if data_context.get("status") == "error":
        print(f"--- ❌ Halting execution due to web scraping error: {data_context.get('error_message')} ---")
        return
    
    # 1c. Get the AI-generated code for creating the DataFrame from the HTML
    creation_code = get_dataframe_creation_code(user_request, data_context['html_content'])
    
    # 1d. Execute the creation code to get the raw DataFrame
    data_context = python_interpreter(code=creation_code, data_context=data_context)
    if data_context.get("status") == "error":
        print(f"--- ❌ Halting execution due to DataFrame creation error: {data_context.get('error_message')} ---")
        return
        
    print("\n--- ✅ Raw DataFrame created successfully! ---")
    print(" Raw DataFrame Preview :")
    print(data_context['df'].head())
    
    # ========== Phase 2: DYNAMIC PLANNING ==========
    print("\n--- Phase 2: Dynamic Planning ---")
    df = data_context['df']
    df_preview = {"columns": df.columns.tolist(), "head": df.head(10).to_string()}
    
    final_plan = create_dynamic_plan(user_request, df_preview)
    
    # ========== Phase 3: FINAL EXECUTION ==========
    if final_plan:
        print("\n--- Phase 3: Final Execution ---")
        final_context = execute_plan(user_request, final_plan, data_context)
        return final_context
    else:
        print("--- ❌ Halting: Could not generate a final plan. ---")
        return data_context


if __name__ == '__main__':
    user_request = """
    Scrape the list of highest grossing films from Wikipedia at the URL https://en.wikipedia.org/wiki/List_of_highest-grossing_films.
    Then, create and clean the DataFrame.
    Finally, use the `answer_generator` to print a JSON object with two keys:
    1. "movies_over_2.5_billion": The integer number of movies that grossed over $2.5 billion.
    2. "average_gross_2019": The average gross of movies released in 2019, as a float.
    """
    final_context = run_agent(user_request)
    print("\n--- Final Results ---")
    if 'final_answer' in final_context:
        print("\n✅ Final Answer from Agent:")
        try: print(json.dumps(json.loads(final_context['final_answer']), indent=2))
        except (json.JSONDecodeError, TypeError): print(final_context['final_answer'])
    elif 'error' in final_context:
        error_message = final_context.get('error_message', final_context.get('error'))
        print(f"\nAn error occurred: {error_message}")
    elif 'df' in final_context and not final_context['df'].empty:
        print("\nExecution finished, but no final answer was generated. Here is the final DataFrame:")
        print(final_context['df'].head())