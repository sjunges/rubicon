FROM sjunges/stormpy:1.6.3

RUN mkdir /opt/rubicon
WORKDIR /opt/rubicon

ENV VIRTUAL_ENV=/opt/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python setup.py install



