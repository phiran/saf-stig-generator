FROM chef/inspec:latest

WORKDIR /app

# Install Python for the MCP server
RUN apk add --no-cache python3 py3-pip

# Accept Chef license
ENV CHEF_LICENSE=accept-silent

# Copy Python source code
COPY agents/src/saf_gen/mcp/inspec_runner_tool.py /app/
COPY tools/requirements.txt /app/

# Install Python dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

# Create directories for artifacts
RUN mkdir -p /app/artifacts/generated

# Set the default port
EXPOSE 3000

# Start the MCP server
CMD ["python3", "inspec_runner_tool.py"]
