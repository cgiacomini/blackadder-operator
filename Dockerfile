FROM docker.io/python:3.10

# Set working directory
WORKDIR /usr/src/app

# Create a virtual environment
RUN python3 -m venv venv

# Ensure the virtual environment's pip is up to date
RUN ./venv/bin/pip install --upgrade pip

# Copy requirements file
COPY requirements.txt ./

# Install dependencies using the virtual environment's pip
RUN ./venv/bin/pip install -r requirements.txt

# Copy application code
COPY controller.py ./

# Set the command to run the application
CMD ["./venv/bin/python", "-u", "controller.py"]
