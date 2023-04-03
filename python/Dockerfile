FROM python:3.7

WORKDIR /app

COPY src/. .

RUN pip install pip update
RUN pip install -r requirements.txt

CMD ["python", "chatbot.py"]