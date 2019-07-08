FROM python:3.7
WORKDIR /workdir
ADD . /workdir

RUN wget https://chromedriver.storage.googleapis.com/75.0.3770.90/chromedriver_linux64.zip && \
unzip chromedriver_linux64.zip && chmod 755 chromedriver && mv chromedriver /usr/local/bin && rm chromedriver_linux64.zip

RUN sh -c 'wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -' && \
sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list' && \
apt-get update && apt-get install -y google-chrome-stable libgconf2-4 libnss3-dev



RUN pip install -r requirements.txt

# ENTRYPOINT [ "python", "main.py" ]
