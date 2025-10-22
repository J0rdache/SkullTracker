#!/bin/bash
curl -O https://github.com/opencv/opencv/blob/master/data/haarcascades/haarcascade_frontalface_alt.xml && virtualenv .env && source .env/bin/activate && pip install -r requirements.txt