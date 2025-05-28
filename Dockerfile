FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the utility
COPY aqua_license_util.py .

# Create directory for config files
RUN mkdir -p /root/.aqua

# Set the entrypoint
ENTRYPOINT ["python", "aqua_license_util.py"]

# Default command (show help)
CMD ["--help"]