A simple wrapper to yt-dlp in Python, which download a good enough version of a youtube video, and add some sugar around it.

Good enough meaning the best possible audio track (without DRC), and a 1080p video track. In order to minimize the space taken by the download files, the script applies the following criterias:
- no more than 30fps
- codecs order AV1 > VP9 > H264 (contrary to yt-dlp’s default which downgrades AV1 after H264)
- if 1080p isn’t available for one video, the script select the next best quality

This wrapper can also save a Youtube video as an audio file. In this case, we still don’t want DRC
(Dynamic Range Compression) tracks, obviously. And we select on the bitrate only, because:
- for lossy codecs, bitrate is more important than sample rate
- for music, it was probably recorded in 44.1 kHz
- Youtube’s Opus files all seem to be in 48 kHz, so resampled if the original was in 44.1
- even if Opus is slightly better than AAC at equivalent bitrate, it’s probably cancelled by the resampling

Dependencies:
- yt-dlp installed in ~/.local/bin (if not, you must modify the variable Yt-dlp\_path)
- mediainfo
- ffmpeg

Usage:
- The first argument indicate if you want to download the URL as a video or a music file.
- The second argument specify the URL of a Youtube video. 

ytdlp\_wrapper.py video|music YOUTUBE\_VIDEO\_URL
