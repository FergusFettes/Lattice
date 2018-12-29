import ffmpeg
import os
import re

filenums = [re.findall('([0-9]{3}).png', i) for i in os.listdir('images')]
fileints = [int(i[0]) for i in filter(None, filenums)]

overlay_file = ffmpeg.input('images/watermark.png')
(
    ffmpeg
    .input('images/test{:04d}.png'.format(max(fileints)))
    .overlay(overlay_file)
    .output('images/test{:04d}.png'.format(max(fileints)))
    .run()
)
(
    ffmpeg
    .input('images/test%04d.png')
    .output('images/testt.gif', framerate=5, f='gif')
    .run()
)

for i in range(max(fileints) + 1):
    os.remove('images/test{:04d}.png'.format(i))
