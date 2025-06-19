FROM node:20-bullseye-slim

WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install SAF CLI globally
RUN npm install -g @mitre/saf

# Install FastMCP and other Python dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Copy Python source code
COPY ../agents/src/saf_gen/mcp/saf_generator_tool.py /app/
COPY requirements.txt /app/

# Install Python dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

# Create directories for artifacts
RUN mkdir -p /app/artifacts/generated

# Set the default port
EXPOSE 3000

# Start the MCP server
CMD ["python3", "saf_generator_tool.py"]
