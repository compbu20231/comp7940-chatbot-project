FROM python:3.7

WORKDIR /app

COPY src/. .
RUN chmod 755 ./autorerun.sh
RUN pip install pip update
RUN pip install -r requirements.txt
# CMD ["./autorerun.sh"]
# CMD ["tail", "-f","/dev/null"]
CMD ["python", "chatbot.py"]