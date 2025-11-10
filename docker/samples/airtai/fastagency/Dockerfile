FROM python:3.10
WORKDIR /
RUN apt-get update && apt-get install -y curl
RUN curl -sSL https://install.python-poetry.org | python -
ENV PATH="/root/.local/bin:$PATH"
RUN pip install pytest
RUN pip install pipdeptree
RUN git clone https://github.com/airtai/fastagency.git
RUN mkdir /repo
RUN git config --global --add safe.directory /repo
RUN cp -r /fastagency/. /repo && rm -rf /fastagency/
RUN rm -rf /fastagency
RUN pip install hatch==1.14.0
RUN cd /repo && hatch env create
RUN pip install fastapi==0.115.6 asyncer==0.0.8 websockets==14.1
RUN pip install openai==1.57.4 anthropic==0.40.0 together==1.3.5 markdownify==0.14.1
RUN pip install uvicorn==0.34.0 gunicorn==23.0.0
RUN pip install coverage[toml] pytest==8.3.4 pytest-asyncio==0.25.0 dirty-equals==0.8.0 pytest-rerunfailures==15.0 jsondiff==2.2.1
RUN pip install fastapi_code_generator==0.5.2 bcrypt==4.2.1 mesop==0.13.0 autogen==0.5.3
RUN pip install PyJWT==2.10.1 firebase-admin==6.6.0
RUN pip install passlib[bcrypt]
RUN pip install python-multipart==0.0.19