FROM python:3.12.6-slim-bullseye

# Set timezone for Asia/Phnom_Penh
RUN ln -fs /usr/share/zoneinfo/Asia/Phnom_Penh /etc/localtime && dpkg-reconfigure -f noninteractive tzdata

COPY . /app
WORKDIR /app

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8081

# Start the app using Gunicorn with 4 workers, binding to port 8081, and setting a 300-second timeout
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8081", "app:app", "--timeout", "300"]