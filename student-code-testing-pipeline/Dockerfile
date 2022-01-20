FROM ubuntu:18.04

CMD /bin/bash
#installing packages
RUN apt -y update
RUN apt -y install sudo
RUN apt -y install docker.io
RUN apt -y install valgrind 
RUN apt -y install python3.8 python3.8-dev python3.8-distutils python3.8-venv
RUN apt -y install python3-pip
RUN apt -y install iputils-ping
RUN apt -y install unzip
RUN python3.8 -m pip install bs4 requests
RUN python3.8 -m pip install sqlalchemy 

#user management
#creates user ubuntu
RUN useradd -rm -p '*' -d /home/ubuntu -s /bin/bash -g root -G sudo -u 1000 ubuntu 
#ensures ubuntu does not need a password for sudo
RUN echo "ubuntu ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers 
#creates user cpr
RUN useradd -rm -d /home/cpr -s /bin/bash -u 1001 cpr 
WORKDIR /tmp
RUN mkdir ./dockershared
RUN chown ubuntu ./dockershared
USER ubuntu
ENV USER=ubuntu
ENV DOCKER_ENV=TRUE
WORKDIR /home/ubuntu 
#RUN whoami
#RUN pwd
#preparing pipeline
RUN mkdir eval_pipeline
COPY --chown=ubuntu:root ./eval_pipeline /home/ubuntu/eval_pipeline
RUN chmod 700 eval_pipeline
RUN ls -la 
WORKDIR /home/ubuntu/eval_pipeline/c_util
RUN make 
RUN sudo mv ./htime /usr/bin/htime
RUN ls /usr/bin/unshare #needs to be installed
WORKDIR /home/ubuntu/eval_pipeline
RUN sudo ln -s /home/ubuntu/eval_pipeline/__main__.py /usr/bin/check 

#RUN docker container list #kein sudo??


RUN echo ”Image created”
