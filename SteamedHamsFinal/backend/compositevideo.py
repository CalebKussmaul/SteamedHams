#!/usr/bin/env python3
import os
import shutil
from os.path import join
from .renderer import Renderer
from SteamedHamsFinal.models import Submission
from django.db.models import Q, F, Max
from PIL import Image
import re

class CompositeVideo:
	def __init__(self, cwd = os.getcwd()):
		self.cwd = cwd
		self.NUMFRAMES = 4076/2
		self.DIMS = [(320,240),(640,480)]

	def make_new_video(self):
		self.get_consensus()
		valid = self.validate_frames()
		rendered = False
		if valid:
			rendered = self.render_video()
		else:
			return False

		# Yes it's redundant but extensible
		if rendered:
			return True
		else:
			return False
		
	def get_consensus(self): ########### TODO
		# Refer to Caleb's Submission object and then call Submission.objects
		# You can then get the top voted file path for each frame
		# https://stackoverflow.com/questions/9838264/django-record-with-max-element
		# If none, have it default to staticUrl/original/frame1234.png
		# The path for a Submission object is just 'staticUrl/frame{:04d}/{}.png'.format(frame, id)
		# Once you've identified it, you copy it to 'staticUrl/modified/frame{:04d}.png'.format(frame)
		# If none exists (no submission for that frame), instead copy 
		# from 'staticUrl/original/frame{:04d}.png'.format(frame)

		print('Making consensus')
		topFiles = {}
		for i in range(1, self.NUMFRAMES + 1):
			matches = Submission.objects.filter(frame=i)
			if not bool(matches):
				topFiles[i] = join(self.cwd, 'staticUrl/original/frame{:04d}.png'.format(i))
			else:
				top = matches.order_by(-(F('upvotes')-F('downvotes'))).first()
				topFiles[i] = join(self.cwd, 'staticUrl/submissions/frame{:04d}/{}.png'.format(top.frame, top.id))

		# Now copy them all to modified_temp, with the right frame name
		output_path = join(self.cwd, 'staticUrl/modified_temp')
		if not os.path.exists(output_path):
			os.makedirs(output_path)

		for (frame, path) in topFiles.items():
			framePattern = re.compile('^.*?frame(\\d{4}).*$')
			frameNum = re.search(framePattern, path).group(1)
			destination = join(output_path, 'frame{}.png'.format(frameNum))
			
			try:
				shutil.copy(path, destination) # Copy top file for each frame
			except:
				shutil.copy(join(self.cwd, 'staticUrl/original/frame{:04d}.png'.format(i)),
									destination) # Default to the original frame


	def validate_frames(self):
		print('Validating consensus')
		newFrameDir = join(self.cwd, 'staticUrl/modified_temp')
		newFrames = os.listdir(newFrameDir)
		print('\tChecking for right number of frames')
		if len(newFrames) != self.NUMFRAMES:
			return False
		print('\tChecking all the frames are there')
		for i in range(1, self.NUMFRAMES + 1):
			if 'frame{:04d}.png'.format(i) not in newFrames:
				return False
		print('\tChecking dimensions')
		for frame in newFrames:
			im = Image.open(join(newFrameDir, frame))
			width, height = im.size
			if (width, height) not in self.DIMS:
				return False

		# If right number, full coverage, and right dimensions, then pass the test
		try:
			shutil.rmtree(join(self.cwd, 'staticUrl/modified'))
		except:
			pass # In my defense, it's a hackathon
		shutil.move(newFrameDir, 
			join(self.cwd, 'staticUrl/modified'))
		return True

	def render_video(self):
		print('Rendering')
		renderer = Renderer(self.cwd)
		return renderer.create_video()
