# tools.py
import docker
import pandas as pd
import io
import requests # Make sure requests is imported

def web_scraper(url: str, data_context: dict) -> dict:
    """Scrapes a URL and adds its HTML to the data_context."""
    print(f"--- 🛠️ Tool: web_scraper | URL: {url} ---")
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data_context['html_content'] = response.text
        return data_context
    except requests.RequestException as e:
        data_context['error'] = f"Error scraping URL: {e}"
        return data_context

def python_interpreter(code: str, data_context: dict) -> dict:
    """Executes Python code inside a secure Docker sandbox and returns a status."""
    print(f"--- 🛠️ Tool: Sandboxed Python Interpreter ---")
    
    # Serialize the context (DataFrame and HTML content) to pass into the sandbox
    df_json = data_context.get("df", pd.DataFrame()).to_json(orient='split')
    html_content = data_context.get("html_content", "")

    # This wrapper script now defines the variables the LLM's code will need
    wrapper_code = f"""
import pandas as pd
import io
import sys
from bs4 import BeautifulSoup

# --- Data Loading ---
# The data from our main app is loaded into variables here
df_json = '''{df_json}'''
html_content = '''{html_content}'''
df = pd.read_json(io.StringIO(df_json), orient='split')

# --- Execution ---
# The LLM's code is executed here. It can use 'df' and 'html_content'.
try:
    {code}
except Exception as e:
    print(f"Error: {{e}}", file=sys.stderr)
    sys.exit(1)

# --- Output ---
# The final state of the dataframe is printed to stdout as JSON
if 'df' in locals() and isinstance(df, pd.DataFrame):
    print(df.to_json(orient='split'))
"""
    try:
        client = docker.from_env()
        container_output = client.containers.run(
            "data-analyst-sandbox", command=["python", "-c", wrapper_code],
            remove=True, mem_limit="512m"
        ).decode('utf-8').strip()
        
        print(f"--- Sandbox Raw Output ---\n{container_output}\n------------------------")
        
        # Try to parse the output as a dataframe, if it fails, it's probably text
        try:
            data_context['df'] = pd.read_json(io.StringIO(container_output), orient='split')
            if 'last_code_output' in data_context: del data_context['last_code_output']
        except ValueError:
            data_context['last_code_output'] = container_output

        data_context['status'] = 'success'
        if 'error' in data_context: del data_context['error']
        print("--- ✅ Sandbox execution successful ---")

    except docker.errors.ContainerError as e:
        error_message = e.stderr.decode('utf-8')
        print(f"--- ❌ Error inside the sandbox: {error_message} ---")
        data_context['status'] = 'error'
        data_context['error_message'] = error_message
    except Exception as e:
        error_message = f"An error occurred with Docker: {e}"
        print(f"--- ❌ {error_message} ---")
        data_context['status'] = 'error'
        data_context['error_message'] = error_message
        
    return data_context