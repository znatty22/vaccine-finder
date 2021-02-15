FROM python:3.7
ENV PYTHONUNBUFFERED 1

ENV TZ=America/New_York
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

WORKDIR /app
COPY . /app/
RUN pip install --no-cache-dir -e /app 

CMD ["python", "/app/vaccine_finder/schedule_jobs.py"] 
