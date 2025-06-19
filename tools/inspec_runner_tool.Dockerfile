FROM ruby:3.2-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    lsb-release \
    ca-certificates \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Install InSpec
RUN curl https://packages.chef.io/chef.asc | gpg --dearmor | tee /usr/share/keyrings/chef-archive-keyring.gpg > /dev/null && \
    echo "deb [signed-by=/usr/share/keyrings/chef-archive-keyring.gpg] https://packages.chef.io/repos/apt/stable $(lsb_release -cs) main" | tee /etc/apt/sources.list.d/chef-stable.list && \
    apt-get update && \
    apt-get install -y inspec && \
    rm -rf /var/lib/apt/lists/*

# Accept Chef license
ENV CHEF_LICENSE=accept-silent

# Copy Python source code
COPY ../agents/src/saf_gen/mcp/inspec_runner_tool.py /app/
COPY requirements.txt /app/

# Install Python dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

# Create directories for artifacts
RUN mkdir -p /app/artifacts/generated

# Set the default port
EXPOSE 3000

# Start the MCP server
CMD ["python3", "inspec_runner_tool.py"]
