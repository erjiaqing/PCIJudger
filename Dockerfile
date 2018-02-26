FROM ubuntu:16.04

VOLUME ["/problem", "/code"]

RUN apt-get update && apt-get install software-properties-common -y
RUN add-apt-repository ppa:gophers/archive && apt-get update && apt-get install -y build-essential python3 python3-pip golang-1.9-go mono-complete openjdk-8-jdk fpc libseccomp-dev && pip3 install PyYAML
COPY * /fj/
RUN cd /fj/lrun && make install && adduser --ingroup lrun runner

WORKDIR /fj/
USER runner
ENTRYPOINT ["python3", "main.py"]
