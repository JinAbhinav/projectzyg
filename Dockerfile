# Use an official Python runtime as a parent image
FROM python:3.9-slim-bullseye

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive
# Default Redis URL for RQ worker, assuming 'redis' is the service name in a docker-compose setup
ENV RQ_REDIS_URL="redis://redis:6379/0" 
ENV TOR_SOCKS_HOST="127.0.0.1"
ENV TOR_SOCKS_PORT="9050"
ENV NODE_VERSION=18
# Suppress Playwright's browser download if we are installing Chrome manually
ENV PLAYWRIGHT_BROWSERS_PATH=/dev/null 

WORKDIR /app

# Install system dependencies: curl, git, tor, and Node.js (required by Botasaurus)
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl git tor gnupg ca-certificates wget unzip && \
    # Add NodeSource repository for specified Node.js version
    curl -fsSL https://deb.nodesource.com/setup_${NODE_VERSION}.x | bash - && \
    # Install Node.js
    apt-get install -y nodejs && \
    # Install Google Chrome Stable
    wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && \
    apt-get install -y ./google-chrome-stable_current_amd64.deb && \
    rm google-chrome-stable_current_amd64.deb && \
    # Create a symlink for chrome if botasaurus/playwright needs it in a specific location
    # (though usually /usr/bin/google-chrome or /opt/google/chrome/chrome is fine)
    # Ensure /usr/bin is in PATH (it should be by default)
    # Clean up
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Verify Node.js installation and PATH
RUN echo "Current PATH: $PATH"
RUN which node
RUN node --version
RUN which npm
RUN npm --version
RUN google-chrome --version || echo "Google Chrome check failed but continuing build."
RUN tor --version

# Upgrade pip
RUN pip install --upgrade pip

# --- TorBot installation will be handled by requirements.txt ---
# Python dependencies, including torbot and its own dependencies, are installed via pip.
# Ensure 'torbot' (and potentially its specific dependencies if not well-packaged)
# is correctly listed in requirements.txt.

# Copy the requirements file into the container at /app
COPY ./requirements.txt /app/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -vvv -r requirements.txt

# After pip install, if TorBot provides a CLI command (e.g., 'torbot'), 
# you might want to check its version or that it's runnable.
# We've removed TorBot for now to resolve dependency issues.
# RUN torbot --version || (echo "Failed to get torbot version. Check installation and PATH." && exit 1)

# Copy the rest of the application
COPY . .

# Copy the entire 'seer' application directory into the container at /app/seer
COPY ./seer /app/seer

# --- Tor configuration (optional, if defaults are not sufficient) ---
# You can add a custom torrc file if needed:
# COPY torrc.custom /etc/tor/torrc
# RUN chmod 644 /etc/tor/torrc

# By default, the 'tor' package should configure Tor to run and listen on 127.0.0.1:9050.

# Command to run the RQ worker and ensure Tor is started.
# A more robust way to manage multiple processes like Tor and RQ worker is to use a supervisor program (e.g., supervisord).
CMD service tor start && echo "Tor service started/checked." && rq worker -u ${RQ_REDIS_URL} crawling 