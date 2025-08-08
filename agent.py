# agent.py 
import pandas as pd
import json
import ast
import inspect
from prompts import user_request
from llm_handler import create_analysis_plan, get_corrected_code
from tools import web_scraper, python_interpreter, answer_generator, data_cleaner

AVAILABLE_TOOLS = {"web_scraper": web_scraper, "python_interpreter": python_interpreter, "answer_generator": answer_generator, "data_cleaner": data_cleaner}
MAX_RETRIES = 3

def execute_plan(user_request: str, plan: list):
    data_context = {"df": pd.DataFrame()}
    plan_str = json.dumps(plan, indent=2)

    for step in sorted(plan, key=lambda x: x['step']):
        tool_name = step.get('tool')
        args = step.get('args', {})
        print(f"\n--- Executing Step {step['step']}: {tool_name} ---")

        if tool_name not in AVAILABLE_TOOLS:
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
            
        tool_function = AVAILABLE_TOOLS[tool_name]
        
        # Prepare all possible arguments any tool might need
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
                    # This check is to prevent infinite loops if the debugger fails
                    if attempt >= MAX_RETRIES - 1:
                        print("--- 🚫 Max retries reached. Failing step. ---")
                        data_context['error'] = f"Max retries reached. Last error: {error_message}"
                        break
                    
                    print(f"--- 🔁 Attempt {attempt + 1} failed. Asking smart debugger for a fix... ---")
                    failed_code = current_args.get("code", "N/A")
                    error_history += f"--- ATTEMPT {attempt + 1} ---\nFAILED CODE:\n{failed_code}\n\nERROR:\n{error_message}\n---\n"
                    # Update the 'code' argument with the corrected code for the next attempt
                    current_args['code'] = get_corrected_code(user_request, plan_str, step['step'], error_history)

            except Exception as e:
                # This catches unexpected crashes in the tool itself
                data_context['status'] = 'error'; data_context['error_message'] = f"Error calling tool '{tool_name}': {repr(e)}"
                break # Exit the loop on a hard crash

        if 'error' in data_context or data_context.get('status') == 'error':
            print(f"Stopping execution due to an unrecoverable error in Step {step['step']}.")
            break
            
    return data_context


if __name__ == '__main__':
    user_request = """
    Scrape the list of highest grossing films from Wikipedia at the URL https://en.wikipedia.org/wiki/List_of_highest-grossing_films.
    Then, create and clean the DataFrame.
    Finally, use the `answer_generator` to print a JSON object with two keys:
    1. "movies_over_2.5_billion": The integer number of movies that grossed over $2.5 billion.
    2. "average_gross_2019": The average gross of movies released in 2019, as a float.
    """
    plan = create_analysis_plan(user_request)
    if plan:
        final_context = execute_plan(user_request, plan)
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