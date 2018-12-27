import requests
import subprocess
import os
from SteamedHamsFinal import secrets

# site = "http://obviouslygrilled.com"
site = "http://localhost:8000"

if not os.path.exists("images"):
    os.makedirs("images")
for i, url in enumerate(requests.get(site+"/images.json/"+secrets.images_password+"/").json()):
    with open("images/frame{:04d}.png".format(i), 'wb') as f:
        f.write(requests.get(url).content)
        print("writing: " + str(i))

yes = subprocess.Popen(['yes'], stdout=subprocess.PIPE)
output = subprocess.Popen(['ffmpeg',
                           '-framerate', '12',
                           '-i', 'images/frame%04d.png',
                           '-i', 'audio.mp4',
                           '-strict', '-2',
                           'rendered.mp4'],
                          stdin=yes.stdout)

