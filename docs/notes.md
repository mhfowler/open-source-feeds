### Deployment Details

Raspberry Pi Image
- basic wifi connectivity stuff, reboot when wifi fails
- postgres database
- redis
- osf-server

Ansible recipe is just for deploying osf-server to ubuntu 16

OSF-canonical will be a particular deployment to AWS
- AWS postgres database
- AWS hosted redis
- staging and production deployment
- only a subset of OSF modules will be installed on the canonical deployment