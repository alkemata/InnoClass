FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the source code
#COPY . .

# Expose the port FastAPI will run on
EXPOSE 8000
ARG BUILD_ENV=server

# Start the FastAPI app with Gunicorn and Uvicorn worker
CMD ["/app/entrypoint.sh"]
