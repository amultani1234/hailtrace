# Use latest Ubuntu
FROM ubuntu:bionic

# No user interaction
RUN export DEBIAN_FRONTEND=noninteractive

# Update base container install
RUN apt-get update
RUN apt-get upgrade -y

# Install python and libs
RUN apt-get install -y apt-utils
RUN apt-get install -y software-properties-common
RUN apt-get install -y python3
RUN apt-get install -y python3-dev
RUN apt-get install -y build-essential

RUN apt-get install -y apt-transport-https
RUN add-apt-repository ppa:ubuntugis/ubuntugis-unstable
RUN apt-get update

# Install GDAL dependencies
RUN apt-get install -y gdal-bin
RUN apt-get install -y python3-pip
RUN apt-get install -y libgdal-dev
RUN apt-get install -y python3-gdal
RUN apt-get install -y locales

# Ensure locales configured correctly
RUN locale-gen en_US.UTF-8
ENV LC_ALL='en_US.utf8'

# Set python aliases for python3
RUN echo 'alias python=python3' >> ~/.bashrc
RUN echo 'alias pip=pip3' >> ~/.bashrc

# Update C env vars so compiler can find gdal
ENV CPLUS_INCLUDE_PATH=/usr/include/gdal
ENV C_INCLUDE_PATH=/usr/include/gdal

RUN mkdir -p /processing

WORKDIR /processing

COPY . /processing

RUN pip3 install numpy

RUN pip3 install semver

RUN pip3 install -r requirements.txt

RUN pip3 install arm_pyart

RUN pip3 install numba

RUN apt-get update

RUN apt-get install -y git

RUN git clone https://github.com/CSU-Radarmet/CSU_RadarTools.git

RUN cd ./CSU_RadarTools && python3 setup.py build && python3 setup.py install && cd .. && rm -rf CSU_RadarTools


