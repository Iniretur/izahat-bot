# Use the official Python base image
FROM python:3.8-slim-buster

# Set the working directory in the container
WORKDIR /app

# Install the dependencies
RUN pip install python-telegram-bot==13.13

# Copy the bot files into the container
COPY . .

# Run the bot script when the container starts
CMD ["python", "izahat-bot.py"]
