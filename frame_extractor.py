from pathlib import Path
import time
import ffmpeg
import json
import random as rand
import argparse


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("file", help="Path to .json dataset")
    parser.add_argument(
        "--test",
        action="store_true",
        help="run extract with returned output, suggested to use a test file",
    )
    parser.add_argument(
        "--vif", action="store_true", help="run extractor on 2025 VIF data"
    )
    args = parser.parse_args()

    print("LOG:", "- Starting Program -")

    if args.vif:
        teams_to_parse = ["VIF"]
    else:
        teams_to_parse = ["BRA", "B/G", "RBK", "VIK", "LSK"]
    try:
        parsed_data = parse_json(args.file, teams_to_parse, args.vif, args.test)
        if args.test:
            print("OUTPUT: (test json data:)", json.dumps(parsed_data, indent=4))
            get_videos(parsed_data, teams_to_parse, "testframes")
        else:
            get_videos(parsed_data, teams_to_parse, "extracted_frames")
    except FileNotFoundError:
        print("ERROR:", "could not find json file to parse")
        return
    except Exception as e:
        print("ERROR:", e)
        return

    print("LOG:", "- Closing -")


def parse_json(filename: str, teams_to_parse: list, vif: bool, test: bool) -> dict:
    print("LOG:", "Parsing json file...")
    try:
        with open(filename, "r", encoding="utf-8") as file:
            data = json.load(file)
    except FileNotFoundError as e:
        raise e

    parsed_data = {}

    for team in teams_to_parse:
        parsed_data[team] = {
            "original_playlist_metadata": data["metadata"],
            "videos": [],
        }

    for k in data["videos"]:
        shortName = k["home_team"]["short_name"]
        if shortName in parsed_data.keys():
            parsed_data[shortName]["videos"].append(k)

    if vif:
        sample = 64
        if test:
            sample = 2

        parsed_data["VIF"]["videos"] = rand.sample(parsed_data["VIF"]["videos"], sample)
        print("Len: ", len(parsed_data["VIF"]["videos"]))

    print("LOG:", "Done parsing json")
    return parsed_data


def get_videos(parsed_data: dict, parsed_teams: list, frames_dir: str):
    print("LOG:", "retriving videos...")
    for team in parsed_teams:
        team_videos = parsed_data[team]["videos"]
        team_metadata = parsed_data[team]
        team = team.replace("/", "_")

        output_dir = Path(frames_dir) / str(team)
        output_dir.mkdir(parents=True, exist_ok=True)
        print("LOG:", f"Extracting Frames for {team}...")

        for i, video in enumerate(team_videos):
            url = video["video_url"]
            output_filename = (
                f"{team}_{video['video_asset_id']}_{video['playlist_id']}_%03d.jpg"
            )
            output_path = output_dir / output_filename
            hihgest_qual = find_highest_qual(url)
            vids_msg = f"Now extracting frames for video: {i + 1}/{len(team_videos)}"
            print(vids_msg.ljust(100), end="\r", flush=True)

            # being nice to the servers
            try:
                # use ffmpeg to grab 1 frame a second from stream
                (
                    ffmpeg.input(url)
                    .filter("fps", fps=1)
                    .output(str(output_path), **{"map": f"0:{hihgest_qual}", "q:v": 2})
                    .run(quiet=True, overwrite_output=True)
                )
            except ffmpeg.Error as e:
                print(e.stderr)
        print()
        print("LOG:", f"Done getting videos for {team}")
        print("LOG:", "Saving metadata")

        metadata_path = output_dir / f"{team}_metadata.json"
        try:
            place_metadata(team_metadata, metadata_path)

        except Exception as e:
            print("ERROR:", "Could not save metadata ", e)

    print("LOG:", "Done getting frames for all teams")


def place_metadata(metadata: dict, metadata_path: Path):
    try:
        with open(metadata_path, "w") as file:
            json.dump(metadata, file, indent=4)
    except Exception as e:
        raise e


def find_highest_qual(url: str) -> int:
    probe = ffmpeg.probe(url)["streams"]
    streams = [s for s in probe if s["codec_type"] == "video"]
    best_stream = streams[0]
    for stream in streams:
        if stream["width"] > best_stream["width"]:
            best_stream = stream

    return best_stream["index"]


if __name__ == "__main__":
    main()
