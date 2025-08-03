# main.py

# Step 1: Import the FastAPI class
# We are importing the main piece of functionality from the fastapi library we installed.
from fastapi import FastAPI

# Step 2: Create an "instance" of the FastAPI application
# This 'app' object is the core of our API. We'll use it to define all our API endpoints.
# Giving it a 'title' is good practice for automatic documentation.
app = FastAPI(title="Data Analyst Agent")

# Step 3: Define an endpoint
# The "@app.get('/')" is a "decorator". It tells FastAPI that the function
# directly below it is in charge of handling requests that come to a specific URL.
# - @app: Use our main app object.
# - .get: This will handle HTTP GET requests (the most common type, used for fetching data).
# - "/": This is the "path". A single slash means the root URL (e.g., http://www.example.com/).
@app.get("/")
def read_root():
  """This is the root endpoint of the API."""
  # Step 4: Return a response
  # FastAPI will automatically convert this Python dictionary into a JSON response,
  # which is the standard language for APIs to communicate in.
  return {"message": "Welcome! The Data Analyst Agent API is running."}