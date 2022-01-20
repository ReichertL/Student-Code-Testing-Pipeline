 
#!/bin/bash
# build images
rm -fr /tmp/dockershared 2> /dev/null
mkdir /tmp/dockershared
sudo docker build -t reference-clone reference-server-clone/.
sudo docker build -t pipeline pipeline/.

#create a shared space where the containers can exchange files



