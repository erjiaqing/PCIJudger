FROM scratch as file_container
COPY /lrun /fj/lrun
COPY /pciutil /fj/pciutil
COPY /lang /fj/lang
COPY ["judger.yaml", "main.py", "mirrorfs.conf", "README", "/fj/"]


FROM ubuntu:16.04
VOLUME ["/problem", "/code"]

################
# build-essential: 主要是为了make
# python3 python3-pip: python
# golang-1.9-go: go
# mono-mcs, mono-runtime: 为了C#，提供基本的mono支持
# openjdk-8-jdk-headless: java
# fpc: FreePascal
# php7.0-cli: PHP 7.0
#
# libseccomp-dev: 为了lrun
# rake: 编译lrun
#
# libbsd-dev, libffi-dev, libgmp3-dev libgmpxx4ldbl: Haskell
################

RUN apt-get update && apt-get install software-properties-common -y && \
    add-apt-repository ppa:gophers/archive && \
    apt-get update && \
    apt-get install -y \
        build-essential \
        python3 python3-pip \
        golang-1.9-go \
        mono-mcs mono-runtime \
        openjdk-8-jdk-headless \
        fpc \
        php7.0-cli \
        libseccomp-dev \
        rake \
        libbsd-dev libffi-dev libgmp3-dev libgmpxx4ldbl && \
    mkdir haskell_tmp && cd haskell_tmp && \
    curl -L https://haskell.org/platform/download/8.2.2/haskell-platform-8.2.2-unknown-posix--core-x86_64.tar.gz | tar x && \
    ./install-haskell-platform.sh && \
    cd / && rm -rf /haskell_tmp && \
    curl -s https://get.sdkman.io | bash && \
    sdk install kotlin && \
    pip3 install PyYAML && \
    rm -rf /var/lib/apt/lists/* && \
    apt clean
COPY --from=file_container /fj /fj
RUN cd /fj/lrun && make install && make clean && useradd runner && adduser runner lrun

WORKDIR /fj/
USER runner
ENTRYPOINT ["python3", "main.py"]
