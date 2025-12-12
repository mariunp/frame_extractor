import json
import ffmpeg


def main():
    find_highest_qual()


def find_highest_qual():
    probe = ffmpeg.probe(
        "https://api.forzify.com/eliteserien/playlist.m3u8/12158:7768000:7793000/Manifest.m3u8"
    )["streams"]
    streams = [s for s in probe if s["codec_type"] == "video"]
    best_stream = streams[0]
    for stream in streams:
        if stream["width"] > best_stream["width"]:
            best_stream = stream

    print(json.dumps(streams, indent=4))


if __name__ == "__main__":
    main()
