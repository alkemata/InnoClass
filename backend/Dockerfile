FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entrypoint script
COPY entrypoint.sh . # Copy the script *before* the RUN commands
RUN chmod +x entrypoint.sh

# Copy the source code
COPY classEngine ./classEngine

# Expose the port FastAPI will run on
EXPOSE 8000

ARG BUILD_ENV=server

# Start script based on BUILD_ENV value
CMD ["./entrypoint.sh"] # Corrected the path to the script
