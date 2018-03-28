#!/usr/bin/env bash

xhost +local:ccad
docker start ccad
docker exec -it ccad /bin/bash