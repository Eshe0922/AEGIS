FROM python:3.10
WORKDIR /
RUN apt-get update && apt-get install -y curl
RUN curl -sSL https://install.python-poetry.org | python -
ENV PATH="/root/.local/bin:$PATH"
RUN pip install pytest
RUN pip install pipdeptree
RUN git clone https://github.com/AIR-Bench/AIR-Bench.git
RUN mkdir /repo
RUN git config --global --add safe.directory /repo
RUN cp -r /AIR-Bench/. /repo && rm -rf /AIR-Bench/
RUN rm -rf /AIR-Bench
RUN pip install datasets>=2.19.0 rich>=13.7.1 pytrec_eval==0.5
RUN pip install black==24.10.0 isort==5.13.2 pytest==8.3.4
ENV PYTHONPATH=/repo