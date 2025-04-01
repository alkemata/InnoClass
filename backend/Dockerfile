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
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh
# Start script based on BUILD_ENV value
CMD ["/app/entrypoint.sh"]
