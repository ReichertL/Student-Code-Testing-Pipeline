###############################################################
# Dockerfile to test the DS C Programmierprojekt eval pipeline
# Based on Ubuntu 18.04
###############################################################
FROM ubuntu:18.04
LABEL maintainer="stephaho@informatik.hu-berlin.de"
RUN apt-get -q update && apt-get -qy upgrade && apt-get -qy install gcc-7 valgrind make
RUN apt-get -q update && apt-get -qy upgrade && apt-get -qy install python3.8 python3-virtualenv
RUN python3.8 -m virtualenv -p /usr/bin/python3.8 venv_cprogrammierung
RUN . /venv_cprogrammierung/bin/activate && pip install pytest numpy bs4 requests unidecode scipy
RUN apt-get -q update && apt-get -qy upgrade && apt-get -qy install sudo time
RUN groupadd -r wheel && echo '%wheel ALL=(ALL) ALL' >> /etc/sudoers
RUN groupadd -g 1000 ubuntu && useradd ubuntu -u 1000 -g 1000 -G wheel -p '' -m
RUN groupadd -g 2000 cpr && useradd cpr -u 2000 -g 2000
RUN . /venv_cprogrammierung/bin/activate && pip install pylint anybadge
