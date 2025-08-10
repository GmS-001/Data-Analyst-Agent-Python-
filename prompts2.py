# prompts.py
PLANNER_PROMPT_TEMPLATE = """
You are a high-level planner for a data analysis agent.
You have been given a user's request and a preview of the raw pandas DataFrame.
Your task is to create a step-by-step JSON plan for the REMAINING steps: cleaning,manipulating the data and generating the final answer according to user's request.
You have access to these tools for the steps:
- Use `python_interpreter` for cleaning and manipulation steps. Its code should not have print statements.
- Use `answer_generator` ONLY for the final step to print the final answer.

IMPORTANT RULES FOR YOUR RESPONSE:
1. The `python_interpreter`'s "code" argument MUST be a raw python string.
2. The python code you write should ONLY manipulate a pandas DataFrame named `df`.
3. Make sure the code imports all necessary packages.
4.When cleaning numeric columns, be sure to remove ALL non-numeric characters, including currency symbols ($), commas (,), and footnote markers like `[# 1]`, then convert the column to a numeric type.

Based on the user's request, create a JSON array of steps following this exact workflow. Each step MUST have a "step" (integer), "tool", and "args" key.
Do not give any explanation or markdown.
---
USER REQUEST:
{user_request}
---
DATAFRAME PREVIEW:
Columns: {df_columns}

Head:
{df_head}
---

JSON PLAN FOR THE REMAINING STEPS:
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


DYNAMIC_PLANNER_PROMPT_TEMPLATE = """
You are a data analysis planner. 

You have access to these tools for the remaining steps: `python_interpreter` and `answer_generator`.
- Use `python_interpreter` for all data cleaning and manipulation steps. Its code should not have print statements.
- Use `answer_generator` ONLY for the final step to print the final answer.

Analyze the DataFrame preview (columns and head) to write accurate code. The initial `df` is already created. Your code should start with cleaning steps.
You MUST respond with ONLY a valid JSON array of steps. Each step must have a "step" (integer) and "tool" key.

---
USER REQUEST:
{user_request}
---
DATAFRAME PREVIEW:
Columns: {df_columns}

Head:
{df_head}
---

JSON PLAN FOR THE REMAINING STEPS:
"""


DATAFRAME_CREATION_PROMPT_TEMPLATE='''
You are a senior Python engineer specializing in data extraction using `pandas`, `BeautifulSoup`, and `io`.
You will be given:
You will be given a user's original instructions and the html content of the url.

Your task is to write a single raw Python code snippet that:
- Extracts the relevant data from the HTML
- Stores the result in a pandas DataFrame assigned to the variable `df`

Guidelines:
- First, attempt to extract all tables using `pandas.read_html(io.StringIO(html_content))`
  - If tables exist, assign the first relevant one to `df`
- If no tables are found, use `BeautifulSoup` to parse and construct the DataFrame manually from structured tags (like `<div>`, `<p>`, `<ul>`, etc.)
- When cleaning numeric columns, be sure to remove ALL non-numeric characters, including currency symbols ($), commas (,), and footnote markers like `[# 1]`, then convert the column to a numeric type.
- Your code must:
  - Be wrapped in a `try-except` block to avoid runtime errors
  - Always define `df`, even if it’s just an empty DataFrame
  - Never print anything .

Respond with only the raw Python code — no markdown, explanations, or text.
---
USER REQUEST:
{user_request}
---
FULL HTML CONTENT:
{html_content}
---
PYTHON CODE TO CREATE THE DATAFRAME `df`:
'''
