FROM python:3.10
WORKDIR /
RUN apt-get update && apt-get install -y curl
RUN curl -sSL https://install.python-poetry.org | python -
ENV PATH="/root/.local/bin:$PATH"
RUN pip install pytest
RUN pip install pipdeptree
RUN git clone https://github.com/alexwlchan/safari-webarchiver.git
RUN mkdir /repo
RUN git config --global --add safe.directory /repo
RUN cp -r /safari-webarchiver/. /repo && rm -rf /safari-webarchiver/
RUN rm -rf /safari-webarchiver
RUN pip install execnet==2.1.1
RUN pip install iniconfig==2.0.0
RUN pip install markupsafe==2.1.5
RUN pip install packaging==24.0
RUN pip install pluggy==1.5.0
RUN pip install pytest==8.3.4
RUN pip install pytest-httpserver==1.1.0
RUN pip install pytest-xdist==3.6.1
RUN pip install werkzeug==3.0.3