# tools.py
import docker
import pandas as pd
import io
import os
import json
import requests
from bs4 import BeautifulSoup

def web_scraper(url: str, data_context: dict) -> dict:
    print(f"--- 🛠️ Tool: web_scraper | URL: {url} ---")
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data_context['html_content'] = response.text
        data_context['status'] = 'success'
    except requests.RequestException as e:
        data_context['error_message'] = f"Error scraping URL: {e}"
        data_context['status'] = 'error'
    return data_context

# In tools.py

def python_interpreter(code: str, data_context: dict) -> dict:
    """
    Executes Python code inside a secure Docker sandbox using the definitive, simplified wrapper.
    """
    print(f"--- 🛠️ Tool: Sandboxed Python Interpreter (Corrected Wrapper) ---")
    
    context_to_pass = {
        'df': data_context.get("df", pd.DataFrame()).to_json(orient='split'),
        'html_content': data_context.get("html_content", "")
    }
    
    host_dir = os.path.abspath(os.path.dirname(__file__))
    temp_file_path_host = os.path.join(host_dir, "temp_context.json")
    
    with open(temp_file_path_host, 'w') as f:
        json.dump(context_to_pass, f)

    # --- THIS IS THE CORRECTED, SIMPLIFIED WRAPPER ---
    # It simply loads data, runs the LLM's code, and outputs the final DataFrame.
    # Any errors will be caught correctly by Docker.
    wrapper_code = f"""
import pandas as pd
import io, sys, os, json
from bs4 import BeautifulSoup

with open('/app/context.json', 'r') as f:
    context = json.load(f)
df = pd.read_json(io.StringIO(context['df']), orient='split')
html_content = context['html_content']

# Execute the LLM's code
{code}

# Output the final state of the dataframe
print(df.to_json(orient='split'))
"""

    try:
        client = docker.from_env()
        container_output = client.containers.run(
            "data-analyst-sandbox",
            command=["python", "-c", wrapper_code],
            volumes={temp_file_path_host: {'bind': '/app/context.json', 'mode': 'ro'}},
            remove=True, mem_limit="512m"
        ).decode('utf-8').strip()
        
        data_context['df'] = pd.read_json(io.StringIO(container_output), orient='split')
        data_context['status'] = 'success'
        if 'error' in data_context: del data_context['error']
        print("--- ✅ Sandbox execution successful ---")

    except docker.errors.ContainerError as e:
        error_message = e.stderr.decode('utf-8').strip()
        print(f"--- ❌ Error inside the sandbox: {error_message} ---")
        data_context['status'] = 'error'; data_context['error_message'] = error_message
    except Exception as e:
        error_message = f"An error occurred with Docker: {e}"; print(f"--- ❌ {error_message} ---")
        data_context['status'] = 'error'; data_context['error_message'] = error_message
    finally:
        if os.path.exists(temp_file_path_host):
            os.remove(temp_file_path_host)
            
    return data_context