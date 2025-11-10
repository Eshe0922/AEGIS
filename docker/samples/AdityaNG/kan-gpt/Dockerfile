FROM python:3.10
WORKDIR /
RUN apt-get update && apt-get install -y curl
RUN curl -sSL https://install.python-poetry.org | python -
ENV PATH="/root/.local/bin:$PATH"
RUN pip install pytest
RUN pip install pipdeptree
RUN git clone https://github.com/AdityaNG/kan-gpt.git
RUN mkdir /repo
RUN git config --global --add safe.directory /repo
RUN cp -r /kan-gpt/. /repo && rm -rf /kan-gpt/
RUN rm -rf /kan-gpt
RUN cd /repo && pip install -e .
RUN pip install requests_mock==1.12.1