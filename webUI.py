import random
import subprocess
import os
import gradio
import gradio as gr
import shutil
import logging
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', stream=sys.stdout)
logger = logging.getLogger(__name__)
logger.info(f"Current directory: {current_dir}")

def convert(segment_length, video, audio, progress=gradio.Progress()):
    if segment_length is None:
        segment_length = 0
    logger.info(f"Converting video: {video}, audio: {audio}, with segment length: {segment_length}")
    os.makedirs('/temp/video', exist_ok=True)  # Ensure this directory exists
    os.makedirs('/temp/audio', exist_ok=True)  # Ensure this directory exists


    if segment_length != 0:
        video_segments = cut_video_segments(video, segment_length)
        audio_segments = cut_audio_segments(audio, segment_length)
        logger.info(f"Video and audio segmented into {len(video_segments)} segments each.")
    else:
        video_path = os.path.join('/temp/video', os.path.basename(video))
        shutil.move(video, video_path)
        video_segments = [video_path]
        audio_path = os.path.join('/temp/audio', os.path.basename(audio))
        shutil.move(audio, audio_path)
        audio_segments = [audio_path]
        logger.info(f"Video and audio moved to temporary paths: {video_path}, {audio_path}")

    processed_segments = []
    for i, (video_seg, audio_seg) in progress.tqdm(enumerate(zip(video_segments, audio_segments))):
        processed_output = process_segment(video_seg, audio_seg, i)
        processed_segments.append(processed_output)
        logger.debug(f"Processed segment {i+1}/{len(video_segments)}")

    output_file = f"/temp/results/output_{random.randint(0, 1000)}.mp4"
    concatenate_videos(processed_segments, output_file)
    logger.info(f"Concatenated video saved to {output_file}")

    # Remove temporary files
    cleanup_temp_files(video_segments + audio_segments)
    logger.debug("Temporary files cleaned up")

    # Return the concatenated video file
    return output_file


def cleanup_temp_files(file_list):
    for file_path in file_list:
        if os.path.isfile(file_path):
            os.remove(file_path)


def cut_video_segments(video_file, segment_length):
    temp_directory = '/temp/audio'
    shutil.rmtree(temp_directory, ignore_errors=True)
    os.makedirs(temp_directory, exist_ok=True)
    segment_template = f"{temp_directory}/{random.randint(0,1000)}_%03d.mp4"
    command = ["ffmpeg", "-i", video_file, "-c", "copy", "-f",
               "segment", "-segment_time", str(segment_length), segment_template]
    subprocess.run(command, check=True)

    video_segments = [segment_template %
                      i for i in range(len(os.listdir(temp_directory)))]
    return video_segments


def cut_audio_segments(audio_file, segment_length):
    try:
        temp_directory = '/temp/video'
        shutil.rmtree(temp_directory, ignore_errors=True)
        os.makedirs(temp_directory, exist_ok=True)
        segment_template = f"{temp_directory}/{random.randint(0,1000)}_%03d.mp3"
        command = ["ffmpeg", "-i", audio_file, "-f", "segment",
                "-segment_time", str(segment_length), segment_template]
        subprocess.run(command, check=True)

        audio_segments = [segment_template %
                        i for i in range(len(os.listdir(temp_directory)))]
    except Exception as e:
        logger.error(f"Failed operation: {e}")
    return audio_segments


def process_segment(video_seg, audio_seg, i):
    logger.info(f"Processing segment {i} - video: {video_seg}, audio: {audio_seg}")
    os.makedirs("/temp/results/", exist_ok=True)
    output_file = f"/temp/results/{random.randint(10,100000)}_{i}.mp4"
    command = ["python", "-u", "inference.py", "--face", video_seg,
               "--audio", audio_seg, "--outfile", output_file]

    # Start the subprocess and specify that you want to capture the output streams
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    # Capture and log stdout
    for line in process.stdout:
        if line:
            logger.info(f"Segment {i} - stdout: {line.strip()}")

    # Capture and log stderr
    for line in process.stderr:
        if line:
            logger.error(f"Segment {i} - stderr: {line.strip()}")

    # Wait for the subprocess to finish and get the exit code
    process.wait()

    return output_file


def concatenate_videos(video_segments, output_file):
    with open("segments.txt", "w") as file:
        for segment in video_segments:
            file.write(f"file '{segment}'\n")
    # Using the -safe 0 option to disable the safety check
    command = ["ffmpeg", "-f", "concat", "-safe", "0", "-i",
               "segments.txt", "-c", "copy", output_file]
    subprocess.run(command, check=True)


with gradio.Blocks(
    title="Audio-based Lip Synchronization",
    theme=gr.themes.Base(
        primary_hue=gr.themes.colors.green,
        font=["Source Sans Pro", "Arial", "sans-serif"],
        font_mono=['JetBrains mono', "Consolas", 'Courier New']
    ),
) as demo:
    with gradio.Row():
        gradio.Markdown("# Audio-based Lip Synchronization")
    with gradio.Row():
        with gradio.Column():
            with gradio.Row():
                seg = gradio.Number(
                    label="segment length (Second), 0 for no segmentation")
            with gradio.Row():
                with gradio.Column():
                    v = gradio.Video(label='SOurce Face')

                with gradio.Column():
                    a = gradio.Audio(
                        type='filepath', label='Target Audio')

            with gradio.Row():
                btn = gradio.Button(value="Synthesize",variant="primary")
            with gradio.Row():
                gradio.Examples(
                    label="Face Examples",
                    examples=[
                        os.path.join("/video-retalking",
                                     "examples/face/1.mp4"),
                        os.path.join("/video-retalking",
                                     "examples/face/2.mp4"),
                        os.path.join("/video-retalking",
                                     "examples/face/3.mp4"),
                        os.path.join("/video-retalking",
                                     "examples/face/4.mp4"),
                        os.path.join("/video-retalking",
                                     "examples/face/5.mp4"),
                    ],
                    inputs=[v],
                    fn=convert,
                )
            with gradio.Row():
                gradio.Examples(
                    label="Audio Examples",
                    examples=[
                        os.path.join("/video-retalking",
                                     "examples/audio/1.wav"),
                        os.path.join("/video-retalking",
                                     "examples/audio/2.wav"),
                    ],
                    inputs=[a],
                    fn=convert,
                )

        with gradio.Column():
            o = gradio.Video(label="Output Video")

    btn.click(fn=convert, inputs=[seg, v, a], outputs=[o])

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', stream=sys.stdout)
logger = logging.getLogger(__name__)
logger.info(f"Current directory: {current_dir}")
demo.queue().launch(server_port=7860, server_name="0.0.0.0", debug=True, show_error=True)
