# agent.py 
import pandas as pd
import ast
from llm_handler import create_analysis_plan
from tools import web_scraper, python_interpreter

AVAILABLE_TOOLS = {"web_scraper": web_scraper, "python_interpreter": python_interpreter}

def execute_plan(user_request: str, plan: list):
    data_context = {"df": pd.DataFrame()}

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
        result_context = tool_function(**args, data_context=data_context)
        data_context.update(result_context)

        # If the step failed, stop the execution.
        if data_context.get('status') == 'error':
            print(f"Stopping execution due to an error in Step {step['step']}.")
            break
            
    print("\n--- ✅ Plan Execution Finished ---")
    return data_context

if __name__ == '__main__':
    user_request = """
    Scrape the list of highest grossing films from Wikipedia at the URL https://en.wikipedia.org/wiki/List_of_highest-grossing_films.
    Then, create a pandas DataFrame from the main table on the page using the scraped HTML content.
    Finally, clean the 'Worldwide gross' column to be a numeric type and the 'Year' column to be a numeric type.
    """
    
    # Per your plan, we no longer cache. We always generate a fresh plan.
    print("--- Generating new plan from LLM... ---")
    plan = create_analysis_plan(user_request)

    if plan:
        final_context = execute_plan(user_request, plan)
        print("\n--- Final Results ---")
        
        if 'df' in final_context and not final_context['df'].empty:
            print("\nFirst 5 rows of the final DataFrame:")
            print(final_context['df'].head())
        else:
            print("\nFinal DataFrame is empty.")
            
        if 'error' in final_context:
            # Print the specific error message from the context
            error_message = final_context.get('error_message', final_context.get('error'))
            print(f"\nAn error occurred: {error_message}")