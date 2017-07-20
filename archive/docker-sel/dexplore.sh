# find ID of your running container:
docker ps

# create image (snapshot) from container filesystem
docker commit 12345678904b5 mysnapshot

# explore this filesystem using bash (for example)
docker run -t -i mysnapshot /bin/bash