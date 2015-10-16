# To get reveal.js running on node on an ubuntu instance

```bash
apt-get install git
git clone --recursive https://github.com/MartinPaulo/faafo_infrastructure.git
curl -o- https://raw.githubusercontent.com/creationix/nvm/v0.29.0/install.sh | bash
source ~/.profile
nvm install v4.2.1
npm install -g grunt-cli
cd faafo_infrastructure/doc/presentation/revealjs/
npm install
```

# To install libcloud

```bash
apt-get install python-pip
pip install apache-libcloud
```

# To create the class snapshot

```bash
sudo -i
apt-get update
apt-get upgrade
apt-get install python-pip
pip install apache-libcloud
apt-get install git
git clone https://github.com/MartinPaulo/faafo_infrastructure.git
```

# To get it all working on the class snapshot

```bash
cd faafo_infrastructure/
cd src
cp faafo.cfg.template faafo.cfg
nano faafo.cfg
python chapter1.py 
python teardown.py
```

# On the worker

logs go to `/var/log/supervisor/`
`top` to monitor the worker

# On the api

```bash
faafo create
faafo create --height 9999 --width 9999 --tasks 5
faafo get --help
faafo list --help
faafo delete --help

for i in $(seq 1 5); do faafo create; done
uptime

# just to see it on a given instance:
ssh -i ~/.ssh/nectar_dev.pem ubuntu@130.56.253.87 uptime
```


