FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy the source code
COPY classEngine ./classEngine
RUN chmod +x ./classEngine/entrypoint.sh
RUN ls -l 
# Expose the port FastAPI will run on
EXPOSE 8000

#ARG BUILD_ENV=server

# Start script based on BUILD_ENV value
CMD ["./entrypoint.sh"]