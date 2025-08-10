# main.py

# Step 1: Import the FastAPI class
# We are importing the main piece of functionality from the fastapi library we installed.
from fastapi import FastAPI, UploadFile, File
from fastapi import FastAPI, UploadFile, File, HTTPException
import agent 
import json
import pandas as pd 

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


@app.post("/analyse/")
async def run_analysis_agent(question_file: UploadFile = File(...)):
    """
    This endpoint receives a user's request via a text file,
    runs the full data analysis agent, and returns the final result.
    """
    try:
        # 1. Read the content of the uploaded file to get the user_request string.
        user_request_bytes = await question_file.read()
        user_request = user_request_bytes.decode('utf-8')
        
        # 2. This is the key step: call the main function from our agent.py script.
        # All the complex logic we built (Seeing, Planning, Acting) happens here.
        final_context = agent.run_agent(user_request)
        
        # 3. The agent returns a context dictionary. We must check what's in it
        #    and prepare a clean, JSON-friendly response for the user.
        if not final_context:
            raise HTTPException(status_code=500, detail="Agent failed to produce a result.")
        
        response_data = {}
        
        # Prioritize sending the final answer if it exists.
        if 'final_answer' in final_context:
            # Try to format the answer as clean JSON if possible
            try:
                response_data['answer'] = json.loads(final_context['final_answer'])
            except:
                response_data['answer'] = final_context['final_answer']

        # If there was an error, report it clearly.
        elif 'error_message' in final_context:
            response_data['error'] = final_context['error_message']
        
        # As a fallback, include a preview of the final DataFrame if no answer was generated.
        df = final_context.get('df')
        if isinstance(df, pd.DataFrame) and not df.empty:
            response_data['dataframe_preview'] = df.head().to_dict(orient='records')

        if not response_data:
             return {"message": "Agent run completed, but no specific answer or error was generated."}
        
        return response_data
            
    except Exception as e:
        # Catch any other unexpected errors during the process
        raise HTTPException(status_code=500, detail=f"An unexpected server error occurred: {repr(e)}")
