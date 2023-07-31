# Use the official Python image as the base image
FROM python:3.8.6

# Set environment variables  PYTHONDONTWRITEBYTECODE 写磁盘的优化  PYTHONUNBUFFERED 输出的优化 best practice建议的
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Create and set the working directory inside the container
WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y netcat

# Install Python dependencies  --no-cache-dir 正常要使用，我的网速慢就用缓存
COPY requirements.txt /app/
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy the Django project files into the container
COPY . /app/

# Set the locale to UTF-8
ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8

# Start the Django development server
CMD ["python", "manage.py", "runserver", "0.0.0.0:8080"]