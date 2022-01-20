#start containers in detached mode, with the same socket so they can see each other. /tmp/dockershared is used as a shread space for file exchanges
sudo docker create -v /var/run/docker.sock:/var/run/docker.sock -v /tmp/dockershared:/host --name gruenau_clone gruenau_clone
#sudo docker run -td --name gruenau_clone -v /var/run/docker.sock:/var/run/docker.sock gruenau_clone
sudo docker run -t -d --name pipeline -v /var/run/docker.sock:/var/run/docker.sock  -v /tmp/dockershared:/tmp/dockershared -v /home/reichert/Software_and_Development/dockerfile_for_evalpipline/pipeline/eval_pipeline:/home/ubuntu/eval_pipeline --network="host" pipeline 

# connect to container via sudo docker exec -it pipeline /bin/bash




#to save state of a container: 
#https://stackoverflow.com/questions/19585028/i-lose-my-data-when-the-container-exits
