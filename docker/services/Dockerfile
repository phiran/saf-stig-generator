# Use an official lightweight Python image.
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy the requirements file into the container at /usr/src/app
COPY requirements.txt ./

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application's code from the host to the container
COPY . .

# Expose the port the app runs on
EXPOSE 8000

# Define the command to run your application
# Replace disa_stig_tool.py with the actual name of your tool's main script
CMD ["fastmcp", "start", "disa_stig_tool.py", "--port", "8000"]