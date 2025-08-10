# Dockerfile

# Use an official, lightweight Python image as our base.
FROM python:3.11-slim

# Set the working directory inside the container.
WORKDIR /app

# Install the Python libraries that the LLM's code will need.
# We'll start with pandas, which is essential for data analysis.
RUN pip install pandas beautifulsoup4 lxml html5lib requests