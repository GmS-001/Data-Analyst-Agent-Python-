DATAFRAME_CREATION_PROMPT_TEMPLATE='''
You are a senior Python engineer specializing in data extraction using `pandas`, `BeautifulSoup`, and `io`.
You will be given:
- A user’s original request
- The full HTML content from the target webpage
Your task:
Write a single raw Python code snippet that:
- Extracts all relevant tabular or structured data from the HTML
- Stores the result in a pandas DataFrame assigned to the variable `df`
Guidelines:
1. First, attempt to extract all tables using `pandas.read_html(io.StringIO(html_content))`
   - If tables exist, assign the first relevant one to `df`
2. If no tables are found, use `BeautifulSoup` to parse and construct `df` manually from structured tags (e.g., `<div>`, `<p>`, `<ul>`, `<ol>`, etc.)
3. Your code must:
   - Be wrapped in a `try-except` block to avoid runtime errors
   - Never print anything
   - Import all necessary modules explicitly
4. Respond with **only** the raw Python code — no markdown, comments, or explanations.
---
USER REQUEST:
{user_request}
---
FULL HTML CONTENT:
{html_content}
---
PYTHON CODE TO CREATE THE DATAFRAME `df`:
'''

PLANNER_PROMPT_TEMPLATE = """
You are a planning module for a production-grade data analysis agent. You have been provided:
1. A user's request.
2. A preview of a raw pandas DataFrame.
Your role: Generate a **valid JSON array** describing the remaining steps needed to clean, manipulate, and analyze the DataFrame in order to fulfill the user's request.
Available tools:
- `python_interpreter`: For cleaning and manipulation steps.
- `answer_generator`: For the final step to return the completed answer.
---
STRICT RULES:
1.Do not include any text, explanations, or markdown before or after the JSON.
2. Each JSON element must have exactly these keys:
   - "step": integer step number (1-based).
   - "about": one line about what the step is doing.
   - "tool": name of the tool to use (`python_interpreter` or `answer_generator`).
   - "args": object containing all arguments for that tool.
3. For `python_interpreter`, the "args" object must contain:
   - "code": a **raw Python string** (double-quoted, with all internal quotes/backslashes escaped for JSON).
   - Use one or more `python_interpreter` steps for ALL data cleaning and preparation. The only goal of these steps is to produce a final, clean DataFrame `df`. This code MUST NOT use `print()`.
4. The Python code must:
   - Only manipulate the pandas DataFrame stored in variable `df`.
   - Do not create new df from existing df in any step.
   - Import all required packages explicitly at the start.
5. When cleaning numeric columns:
   - Remove ALL non-numeric characters, including currency symbols ($), commas (,), and footnote markers like `[# 1]`.
   - Make sure you do not remove actual digits from the numerical column.
   - Then convert the column to a numeric type.
   - You MUST use the exact column names provided in the DataFrame preview.
6. Use the `answer_generator` tool for THE VERY LAST STEP. The code for this tool MUST be a self-contained script that performs the final calculations on the clean `df` and then uses `print()` to output the final answer as a single JSON object. 
7. In all JSON strings (especially the "code" field), escape backslashes as \\ and double quotes as \". Do not output raw backslashes.
---
INPUT:
USER REQUEST:
{user_request}
---
DATAFRAME PREVIEW:
Columns: {df_columns}
---
Head:
{df_head}
---
REQUIRED OUTPUT:
A JSON array following the exact rules above, with no additional text.
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


user_request = """
    Scrape the list of highest grossing films from Wikipedia at the URL https://en.wikipedia.org/wiki/List_of_highest-grossing_films.
    Create a pandas DataFrame from the main table.
    Clean the 'Worldwide gross' column to be a numeric float and the 'Year' column to be a numeric integer.
    Finally, use the `answer_generator` tool to print a JSON object with two keys:
    1. "movies_over_2.5_billion": The integer number of movies that grossed over $2.5 billion.
    2. "average_gross_2019": The average gross of movies released in 2019, as a float.
    """