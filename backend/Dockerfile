FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy entrypoint.sh from classEngine directory
COPY classEngine/entrypoint.sh . # Corrected COPY instruction
RUN chmod +x entrypoint.sh

# Copy the source code
COPY classEngine ./classEngine

# Expose the port FastAPI will run on
EXPOSE 8000

ARG BUILD_ENV=server

# Start script based on BUILD_ENV value
CMD ["./entrypoint.sh"]