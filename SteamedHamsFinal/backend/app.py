#!/usr/bin/env python3
# This file provides a minimal Flask app for testing the backend
# For the main app, we will integrate this logic into the main Django logic

from flask import Flask, send_from_directory
import os
from os.path import join
from .downloader import Downloader
from .renderer import Renderer
from .compositevideo import CompositeVideo

app = Flask(__name__)
cwd = os.getcwd()

@app.route("/")
def hello():
    return "Landing page for steamed hams backend API"


@app.route("/download")
def download():
    downloaded = Downloader().download()
    if downloaded:
    	return 'Successfully downloaded video'
    else:
    	return 'Error: failed to download'

@app.route('/render')
def render():
	renderer = Renderer()
	rendered = renderer.create_video()
	if rendered:
		return send_from_directory(join(cwd, 'staticUrl'), 'output.mp4', as_attachment=True)
	else:
		return 'Error: failed to render'


@app.route('/composite')
def composite():
	composite = CompositeVideo()
	composited = composite.make_new_video()
	if composited:
		return send_from_directory(join(cwd, 'staticUrl'), 'output.mp4', as_attachment=True)
	else:
		return 'Error: failed to composite and render'


if __name__ == '__main__':  # pragma: no cover
    app.run(port=80)