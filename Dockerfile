FROM sjunges/stormpy:1.6.3

RUN mkdir /opt/rubicon
WORKDIR /opt/rubicon

ENV VIRTUAL_ENV=/opt/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# install dice

RUN apt-get install -y ocaml opam

RUN opam init --disable-sandboxing --yes

RUN eval $(opam env)

RUN opam switch create 4.09.0

RUN opam install --yes depext

RUN opam depext --yes mlcuddidl

RUN opam pin add --yes dice git+https://github.com/SHoltzen/dice.git#65aff8f

RUN eval $(opam env)


COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python setup.py install

RUN mkdir /opt/rubicon/dice-examples
RUN mkdir /opt/rubicon/factory
