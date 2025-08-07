# agent.py 
import pandas as pd
import json
import ast
import inspect
from prompts import user_request
from llm_handler import create_analysis_plan, get_corrected_code
from tools import web_scraper, python_interpreter, answer_generator

AVAILABLE_TOOLS = {"web_scraper": web_scraper, "python_interpreter": python_interpreter, "answer_generator": answer_generator}
MAX_RETRIES = 3
def execute_plan(user_request: str, plan: list):
    data_context = {"df": pd.DataFrame()}
    plan_str = json.dumps(plan, indent=2) # For passing the full plan to the debugger

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
        tool_params = inspect.signature(tool_function).parameters
        valid_args = {name: value for name, value in args.items() if name in tool_params}

        # The self-correction loop is used for any tool that runs code
        if tool_name in ['python_interpreter', 'answer_generator']:
            current_code = args.get("code")
            error_history = ""
            for attempt in range(MAX_RETRIES):
                result_context = tool_function(code=current_code, data_context=data_context)
                if result_context.get('status') == 'success':
                    data_context.update(result_context)
                    break # Success, exit the retry loop
                else:
                    error_message = result_context.get('error_message', 'An unknown error occurred.')
                    error_history += f"--- ATTEMPT {attempt + 1} ---\nFAILED CODE:\n{current_code}\n\nERROR:\n{error_message}\n---\n"
                    if attempt < MAX_RETRIES - 1: # Check if we have retries left
                        print(f"--- 🔁 Attempt {attempt + 1} failed. Asking smart debugger for a fix... ---")
                        current_code = get_corrected_code(user_request, plan_str, step['step'], current_code, error_history)
                    else:
                        print("--- 🚫 Max retries reached. Failing step. ---")
                        data_context['error'] = f"Max retries reached. Last error: {error_message}"
        else: # For simple tools like web_scraper
            try:
                result_context = tool_function(**valid_args, data_context=data_context)
                data_context.update(result_context)
            except Exception as e:
                data_context['status'] = 'error'; data_context['error_message'] = f"Error calling tool '{tool_name}': {e}"

        if data_context.get('status') == 'error' or 'error' in data_context:
            print(f"Stopping execution due to an unrecoverable error in Step {step['step']}.")
            break
            
    print("\n--- ✅ Plan Execution Finished ---")
    return data_context



if __name__ == '__main__':

    print("--- Generating new plan from LLM... ---")
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