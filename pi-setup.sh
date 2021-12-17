#! /bin/bash

sudo iptables -t nat -I OUTPUT -p tcp -d 127.0.0.1 --dport 80 -j REDIRECT --to-ports 5005
sudo iptables -t nat -I PREROUTING -p tcp --dport 80 -j REDIRECT --to-ports 5005
