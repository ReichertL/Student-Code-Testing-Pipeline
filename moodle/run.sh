

sudo docker pull bitnami/moodle:latest
sudo docker build -t bitnami/moodle:latest 'https://github.com/bitnami/bitnami-docker-moodle.git#master:3/debian-10'
#curl -sSL https://raw.githubusercontent.com/bitnami/bitnami-docker-moodle/master/docker-compose.yml > docker-compose.yml
sudo docker-compose up -d

#site is at : http://127.0.0.1:80
# user #bitnami

#student1: Password#1
#student2
