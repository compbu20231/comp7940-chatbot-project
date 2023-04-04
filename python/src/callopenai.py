import openai
import os

def checkOpenAI4(message):
    openai.api_key = os.environ['OPENAI_API_KEY']
    response = openai.Completion.create(
        model = "gpt-3.5-turbo",
        prompt=f"The following is a conversion with an AI assistant. The assistant is helpful, creative, clever, and very friendly.\n\nHuman: Hello, who are you?\nAI: I am an AI created by OpenaAI. How can I help you today?\n\nHuman:{message}\nAI:",
        temperature=0.9,
        max_tokens=100,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0.6,
        stop=["\n", " Human:", " AI:"]
    )
    AIResponse = response.choices[0].text.replace("\n","")
    return AIResponse


def checkOpenAI(message):
    # config = configparser.ConfigParser()
    # config.read('config.ini')
    # openai.api_key = config['OPENAI']['OPENAI_API_KEY']
    openai.api_key = os.environ['OPENAI_API_KEY']
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": message},
        ],
        temperature=0.9,
        max_tokens=100,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0.6,
    )
    return response['choices'][0]['message']['content']