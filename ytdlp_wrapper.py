#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# ytdlp_wrapper 1.0

#############################################################
# This script needs the following programs:
# - yt-dlp (if it is not installed in ~/.local/bin you must modify the variable Yt-dlp_path)
# - mediainfo
# - ffmpeg
#############################################################

import sys
import subprocess
import os
import fnmatch
import re



def Smooth_string(String):

	# Remove line breaks
	# Another method: " ".join(String.split())
	String.replace('\n', ' ').replace('\r', '')

	# Remove hyphens outside of compound words
	String = String.replace(' - ', '_')

	# Replace dots and spaces with underscores
	String = String.replace(' ', '.').replace('.', '_')

	# Replace multiple _ by only one
	String = re.sub(r'_+', '_', String)

	# Capitalize the first letter and convert the rest to lowercase
	String = String[0].upper() + String[1:].lower()

	return String



def Download_youtube_file(Ytdlp_path, Ytdlp_args, URL):

	# Run the download command with real-time output display
	Download_process = subprocess.Popen(Ytdlp_path + Ytdlp_args + URL, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

	# Extract the file name of the downloaded audio
	File_already_present = False
	Output_filename = None
	for Line in Download_process.stdout:
		# Print each line as it is received
		print(Line, end="")
		if 'has already been downloaded' in Line:
			File_already_present = True
		if ': Downloading 1 format(s): ' in Line:
			Track_format = Line.split('Downloading 1 format(s): ')[1].strip()
		if '[download] Destination: ' in Line:
			Output_filename = Line.split('Destination: ')[1].strip()
		if '[Merger] Merging formats into ' in Line:
			Output_filename = Line.split('Merging formats into ')[1].strip().strip('"')

	Download_process.wait()

	# If yt-dlp exited because the file was already downloaded
	if File_already_present:
		sys.exit(1)
	if Download_process.returncode != 0:
		print("Problem while downloading the file.")
		sys.exit(1)
	if not Output_filename:
		print("Could not determine the output file name.")
		sys.exit(1)

	# .+ greedy (e.+d = |extend cup end|)
	# .+? reluctant (e.+?d = |extend| cup |end|)
	Match = re.search('(.+?)—(.+?)—(.+$)', Output_filename)
	if Match.group(1): Channel = Match.group(1)
	else: Channel = "Unknown"
	if Match.group(2): Title = Match.group(2)
	else: Title = "Unknown"
	if Match.group(3): Reminder = Match.group(3)
	else: Reminder = "Unknown"
	Smoothed_filename = Smooth_string(Channel) + "—" + Smooth_string(Title) + "—" + Reminder

	os.rename(Output_filename, Smoothed_filename)
	print("Downloaded file: " + Smoothed_filename)
	print()

	return (Smoothed_filename, Track_format)



def Merge_video(Video_file, Video_format, Audio_file, Audio_format, Output_filename):

	Merge_command = "ffmpeg -i '" + Video_file + "' -i '" + Audio_file + "' -map 0:v:0 -map 1:a:0 -c:v copy -c:a copy '" + Output_filename

	try:
		print("Merging tracks…")
		subprocess.run(Merge_command, shell=True, check=True, stdout = subprocess.DEVNULL, stderr = subprocess.DEVNULL)
	except subprocess.CalledProcessError as e:
		print(f"Error while merging the tracks: {e}")
		sys.exit(1)

	print("Merged " + Video_format + "+" + Audio_format + " into " + Output_filename)
	os.remove(Video_file)
	os.remove(Audio_file)



def Extract_audio(Audio_file, Audio_format):

	MediaInfo_command = "mediainfo '" + Audio_file + "' | grep -A 2 '^Audio$' | egrep '^Format\s+:'"

	try:
		MediaInfo_process = subprocess.run(MediaInfo_command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	except subprocess.CalledProcessError as e:
		print(f"Error: {e}")
		sys.exit(1)

	# Get the codec name from MediaInfo’s output
	MediaInfo_output = MediaInfo_process.stdout.decode('utf-8').strip()
	if "Format" in MediaInfo_output:
		Codec_name = MediaInfo_output.split(":")[1].strip().lower()
	else:
		print("Could not determine the audio codec.")
		sys.exit(1)

	print("Detected audio codec: " + Codec_name)

	if Audio_file.lower().endswith(".m4a"):
		print(Audio_file + " is already a m4a. No need to create a new file.")
	else:
		# Determine the output file extension based on the codec
		if fnmatch.fnmatch(Codec_name, "aac*"):
			Output_extension = "m4a"
		elif Codec_name == "vorbis":
			Output_extension = "ogg"
		elif Codec_name == "mpeg audio":
			Output_extension = "mp3"
		else:
			Output_extension = Codec_name
	
		Base_name = os.path.splitext(Audio_file)[0]
		Output_filename = Base_name + "." + Output_extension
		Extract_command = "ffmpeg -i '" + Audio_file + "' -vn -acodec copy '" + Output_filename + "'"
		try:
			print("Extracting the audio track…")
			subprocess.run(Extract_command, shell=True, check=True, stdout = subprocess.DEVNULL, stderr = subprocess.DEVNULL)
		except subprocess.CalledProcessError as e:
			print(f"Error while extracting the audio track: {e}")
			sys.exit(1)

		print(Audio_format + " extracted to " + Output_filename)
		os.remove(Audio_file)



if __name__ == "__main__":

	Ytdlp_path = "~/.local/bin/yt-dlp"

	if len(sys.argv) != 3:
		print("Usage: python script.py video|music <youtube_video_url>")
		sys.exit(1)
	Action = sys.argv[1]
	# TODO if the URL isn’t correct, yt-dlp will fail anyway. But we may as well check it here
	# first, with a regexp or something, to avoid ringing Youtube with an useless download.
	URL = sys.argv[2]

	if Action == "video":
		
		Characters_to_delete_for_videos = "'[?!,:\"«»/|()\[\]#—*<>\\\\]'"
		Replace_args = "\
			--replace-in-metadata 'title' " + Characters_to_delete_for_videos + " '' \
			--replace-in-metadata 'title' \"'\" '’' \
			--replace-in-metadata 'uploader' " + Characters_to_delete_for_videos + " '' \
			--replace-in-metadata 'uploader' \"'\" '’'"

		# res:1080 prefers larger videos, but no larger than 1080p and the smallest video if there
		# are no videos less than 1080p.
		Ytdlp_args = " --ignore-config --no-mtime \
			--format bestvideo* --format-sort res:1080,vcodec:av01,fps:30 \
			-o '%(uploader)s—%(title)s—%(id)s.%(ext)s' " \
			+ Replace_args + " "

		Video_file, Video_format = Download_youtube_file(Ytdlp_path, Ytdlp_args, URL)
		Output_filename = os.path.splitext(Video_file)[0] + ".mkv'"
		os.rename(Video_file, "Video—" + Video_file)
		Video_file = "Video—" + Video_file

		Ytdlp_args = " --ignore-config --no-mtime \
			--format bestaudio[format_id!$=-drc] \
			-o '%(uploader)s—%(title)s—%(id)s.%(ext)s' " \
			+ Replace_args + " "

		Audio_file, Audio_format = Download_youtube_file(Ytdlp_path, Ytdlp_args, URL)
		os.rename(Audio_file, "Audio—" + Audio_file)
		Audio_file = "Audio—" + Audio_file

		Merge_video(Video_file, Video_format, Audio_file, Audio_format, Output_filename)

	elif Action == "music":

		Characters_to_delete_for_musics = "'[?!,:\"/|\[\]#—*<>\\\\]'"

		# The doc says “Do not use --format bestaudio*” (with the star operator)
		# cf. https://github.com/yt-dlp/yt-dlp?tab=readme-ov-file#format-selection
		# We select on bitrate only (see README)
		Ytdlp_args = " --ignore-config --no-mtime \
			--format bestaudio[format_id!$=-drc] --format-sort abr \
			-o '%(uploader)s—%(title)s—%(id)s.%(ext)s' \
			--replace-in-metadata 'title' " + Characters_to_delete_for_musics + " '' \
			--replace-in-metadata 'title' \"'\" '’' \
			--replace-in-metadata 'title' '&' 'and' \
			--replace-in-metadata 'uploader' " + Characters_to_delete_for_musics + " '' \
			--replace-in-metadata 'uploader' \"'\" '’' \
			--replace-in-metadata 'uploader' '&' 'and' "

		Audio_file, Audio_format = Download_youtube_file(Ytdlp_path, Ytdlp_args, URL)
		Extract_audio(Audio_file, Audio_format)

	#TODO
	#elif Action == "twitter":
	# Filename too long → try “-o %(title).200B.%(ext)s”

	else:
		print("Usage: ytdlp_wrapper.py video|music <youtube_video_url>")
		sys.exit(1)
