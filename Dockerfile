FROM python:3.9.6
WORKDIR /workdir

RUN wget https://chromedriver.storage.googleapis.com/81.0.4044.69/chromedriver_linux64.zip && \
unzip chromedriver_linux64.zip && chmod 755 chromedriver && mv chromedriver /usr/local/bin && rm chromedriver_linux64.zip

RUN sh -c 'wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -' && \
sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list' && \
apt-get update && apt-get install -y google-chrome-stable=81.0.4044.129-1 libnss3-dev

ADD requirements.txt /workdir

RUN pip install -r requirements.txt

ADD . /workdir

ENTRYPOINT [ "python", "main.py" ]
