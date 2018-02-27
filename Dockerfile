FROM ubuntu:16.04

VOLUME ["/problem", "/code"]

RUN apt-get update && apt-get install software-properties-common -y
RUN add-apt-repository ppa:gophers/archive && apt-get update && apt-get install -y build-essential python3 python3-pip golang-1.9-go mono-mcs mono-runtime openjdk-8-jdk fpc php7.0-cli libseccomp-dev rake && pip3 install PyYAML
COPY /lang /fj/lang
COPY /lrun /fj/lrun
COPY /pciutil /fj/pciutil
COPY ["judger.yaml", "/fj/"]
COPY ["main.py", "/fj/"]
RUN cd /fj/lrun && make install && useradd runner && adduser runner lrun

WORKDIR /fj/
USER runner
ENTRYPOINT ["python3", "main.py"]
