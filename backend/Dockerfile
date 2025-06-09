FROM python:3.11-slim

# 2. Set the working directory inside the container.
WORKDIR /app

# 3. Set environment variables to prevent Python from writing .pyc files.
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# 4. Copy the requirements file and install dependencies.
# This is done before copying the rest of the code to leverage Docker's layer caching.
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 5. Copy the application code into the container.
COPY . .

# 6. Expose the port the app will run on.
EXPOSE 8000

# 7. Command to run the application using uvicorn.
# The --host 0.0.0.0 is crucial to make it accessible from outside the container.
# The --reload flag enables automatic reloading on code changes.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]