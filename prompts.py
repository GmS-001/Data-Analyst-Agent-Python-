# prompts.py
PLANNER_PROMPT_TEMPLATE = """
You are a high-level planner for a data analysis agent. Your goal is to create a step-by-step plan based on a user's request.
You have access to the following tools: `web_scraper`, `python_interpreter`, `data_cleaner`, and `answer_generator`.

The standard workflow is always:
1. `web_scraper`: To get the HTML from a URL.
2. `python_interpreter`: To run code that creates the initial, raw DataFrame from the HTML.
3. `data_cleaner`: A specialized tool that will clean the raw DataFrame.
4. `answer_generator`: To perform final calculations on the clean DataFrame and print the final answer.
---
IMPORTANT RULES FOR YOUR RESPONSE:
1. The `python_interpreter`'s "code" argument MUST be a raw python string.
2. The python code you write should ONLY manipulate a pandas DataFrame named `df`.
3. The python code has access to two pre-loaded variables:
   - `html_content`: A string containing the full HTML from the `web_scraper` tool.
   - `df`: The pandas DataFrame, which is empty initially.
4. The first python step after scraping MUST create the dataframe using the `html_content` variable, like this: `df = pd.read_html(io.StringIO(html_content))[0]`
---
Based on the user's request, create a JSON array of steps following this exact workflow. Each step MUST have a "step" (integer), "tool", and "args" key.
The `python_interpreter` and `answer_generator` tools require a "code" argument.
Do not give any explanation or markdown.
---
USER REQUEST:
{user_request}
"""

DEBUGGER_PROMPT_TEMPLATE = """
You are an expert Python debugging assistant. Your goal is to fix a broken piece of Python code.

You will be provided with the full context of the task:
1. The original user request.
2. The full, multi-step plan that was generated.
3. The specific step in the plan that failed.
4. The Python code from the failing step,including a history of previously failed attempts. 
5. A detailed error message, which may include the state of the pandas DataFrame (its columns and head) at the time of the error.

Analyze all of this information to understand the context and the error.Analyze this history to avoid repeating mistakes. Your task is to return ONLY the corrected, raw Python code for the failing step. Do not add any explanations or markdown.
A common error is a `KeyError`, which means the code is using a column name that doesn't exist. Carefully check the DataFrame's columns in the diagnostic information to find the correct name.

---
CONTEXT:
Original User Request: {user_request}
Full Plan: {full_plan}
Failed Step Number: {failed_step_number}
---

FAILED CODE:
---
{failed_code}
---

History of Failed Attempts:
---
{error_history}
---

CORRECTED PYTHON CODE:
"""

CLEANER_PROMPT_TEMPLATE = """
You are a data cleaning expert.
You will be given a user's original instructions and a preview of a messy pandas DataFrame (including its columns and the first few rows).
1.Your task is to write a Python script that cleans this specific DataFrame according to user's original instructions.
2.The script should not have any print statements.
3.The cleaned DataFrame must be assigned back to a variable named `df`.
4.Make sure the code include every necessary package needed to clean data.
5.When cleaning numeric columns, be sure to remove ALL non-numeric characters, including currency symbols ($), commas (,), and footnote markers like `[# 1]`, then convert the column to a numeric type.
6.Do not give any explanation or markdown.
---
USER'S original INSTRUCTIONS:
{user_request}
---
DATAFRAME PREVIEW (METADATA):
Columns: {df_columns}

Head:
{df_head}
---

PYTHON SCRIPT TO CLEAN THE DATAFRAME `df`:
"""

user_request = """
    Scrape the list of highest grossing films from Wikipedia at the URL https://en.wikipedia.org/wiki/List_of_highest-grossing_films.
    Create a pandas DataFrame from the main table.
    Clean the 'Worldwide gross' column to be a numeric float and the 'Year' column to be a numeric integer.
    Finally, use the `answer_generator` tool to print a JSON object with two keys:
    1. "movies_over_2.5_billion": The integer number of movies that grossed over $2.5 billion.
    2. "average_gross_2019": The average gross of movies released in 2019, as a float.
    """