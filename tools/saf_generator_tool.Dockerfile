FROM node:20-alpine

WORKDIR /app

# Install dependencies
RUN apk add --no-cache \
  curl \
  git \
  python3 \
  py3-pip

# Install SAF CLI globally
RUN npm install -g @mitre/saf

# Copy Python source code
COPY agents/src/saf_gen/mcp/saf_generator_tool.py /app/
COPY tools/requirements.txt /app/

# Install Python dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

# Create directories for artifacts
RUN mkdir -p /app/artifacts/generated

# Set the default port
EXPOSE 3000

# Start the MCP server
CMD ["python3", "saf_generator_tool.py"]
