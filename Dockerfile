FROM python:3.11-slim

# Firefox + geckodriver ইনস্টল
RUN apt-get update && apt-get install -y     firefox-esr     wget     curl     unzip     && rm -rf /var/lib/apt/lists/*

# Geckodriver ইনস্টল
RUN GECKODRIVER_VERSION=0.34.0 &&     wget -q https://github.com/mozilla/geckodriver/releases/download/v$GECKODRIVER_VERSION/geckodriver-v$GECKODRIVER_VERSION-linux64.tar.gz &&     tar -xzf geckodriver-v$GECKODRIVER_VERSION-linux64.tar.gz -C /usr/local/bin &&     rm geckodriver-v$GECKODRIVER_VERSION-linux64.tar.gz

# কাজের ফোল্ডার
WORKDIR /app

# কোড কপি করো
COPY . /app

# পাইথন প্যাকেজ ইন্সটল
RUN pip install --no-cache-dir -r requirements.txt

# বট চালাও
CMD ["python", "tttt - Copy.py"]
