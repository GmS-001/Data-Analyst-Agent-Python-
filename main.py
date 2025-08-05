# main.py

# Step 1: Import the FastAPI class
# We are importing the main piece of functionality from the fastapi library we installed.
from fastapi import FastAPI, UploadFile, File
from llm_handler import get_gemini_response

# Step 2: Create an "instance" of the FastAPI application
# This 'app' object is the core of our API. We'll use it to define all our API endpoints.
# Giving it a 'title' is good practice for automatic documentation.
app = FastAPI(title="Data Analyst Agent")

@app.get("/")
def read_root():
  """This is the root endpoint of the API."""
  # Step 4: Return a response
  # FastAPI will automatically convert this Python dictionary into a JSON response,
  # which is the standard language for APIs to communicate in.
  return {"message": "Welcome! The Data Analyst Agent API is running."}


# Define our new endpoint to handle the analysis task
# We use @app.post since we expect data to be sent to the server.
# The 'async' keyword makes the endpoint asynchronous. This is crucial for
# long-running tasks like calling an LLM, as it prevents the server from
# freezing while it waits for a response.
@app.post("/analyse/")
async def analyse_data(question_file: UploadFile = File(...)):
  """
  Accepts a question file, reads it, and returns its content.
  This is the first step of our data analyst agent.
  """
  contents_bytes = await question_file.read()
  # The file content is read as 'bytes', so we need to 'decode' it
  # into a human-readable string using UTF-8 encoding.
  task_description = contents_bytes.decode('utf-8')
  
  print(f"Sending prompt to LLM: '{task_description}'")
  llm_response = get_gemini_response(task_description)
  print("LLM response received.")

  return {
      "filename": question_file.filename,
      "task_received": task_description,
      "llm_analysis": llm_response 
  }