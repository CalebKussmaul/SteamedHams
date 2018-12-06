#!/usr/bin/env python3

import os
from os.path import join
import subprocess
from pytube import YouTube

class Downloader:
	def __init__(self, cwd=os.getcwd()):
		self.cwd = cwd
		self.url = 'https://www.youtube.com/watch?v=Y4lnZr022M8'
		self.yt = YouTube(self.url)
		streams = self.yt.streams

		self.video = streams.filter(adaptive=True).filter(mime_type='video/mp4').first()
		self.audio = streams.filter(adaptive=True).filter(mime_type='audio/mp4').first()

	def download(self):
		if not os.path.exists(join(self.cwd,'staticUrl')):
			os.makedirs(join(self.cwd, 'staticUrl'))
			os.makedirs(join(self.cwd, 'staticUrl/original'))
			os.makedirs(join(self.cwd, 'staticUrl/modified'))
		if not os.path.exists(join(self.cwd,'staticUrl/video.mp4')):
			print('Downloading video')
			self.video.download(join(self.cwd,'staticUrl'), 'video')
		if not os.path.exists('staticUrl/audio.mp4'):
			print('Downloading audio')
			self.audio.download(join(self.cwd,'staticUrl'), 'audio')

		self.video_to_frames()
		return True

	def video_to_frames(self):
		print('Video to original')
		if not os.path.exists(join(self.cwd,'staticUrl/original')):
			os.makedirs(join(self.cwd,'staticUrl/original'))
		subprocess.call(['ffmpeg', '-i', 'staticUrl/video.mp4', '-vf', 'fps=12, scale=640:480',
			'staticUrl/original/frame%04d.png'],
			cwd = self.cwd)


if __name__ == '__main__':
	Downloader().download()