# Dockerfile

# 1. Base image
FROM python:3.11-slim

# 2. Set working directory
WORKDIR /app

# 3. Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copy source code và file env
COPY . .
COPY .env .env

# 5. Expose the port Uvicorn will run on
EXPOSE 10000

# 6. Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]