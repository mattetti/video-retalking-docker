# docker setup for https://github.com/OpenTalker/video-retalking

## pre requirements

- Windows 11
- WSL 2
- Linux distribution (Ubuntu 20.04 LTS or later)
- Docker Desktop for windows
- nvidia GPU
- nvidia-container-toolkit installed in WSL

## check environment to make sure it's ready to go

- Start a new terminal under your linux distribution
- run `nvidia-smi` to make sure the toolkit is installed and a GPU is available.

## Download the video-retalking weights

As per https://github.com/OpenTalker/video-retalking/blob/main/README.md you need download the [pretrained models](https://drive.google.com/drive/folders/18rhjMpxK8LVVxf7PI6XwOidt8Vouv_H0?usp=share_link) and put them in the checkpoints folder.

## Build the image

- From a windows terminal, run `docker build . -t lipsync` to build the docker image
- If everything built well, run ` docker run -v ./checkpoints:/video-retalking/checkpoints -v ./temp:/temp --rm -it -p 7860:7860 --gpus all lipsync:latest` to start the container
- you need to replace the volumes with the correct paths to the checkpoints and temp folders

## Run everything (using docker compose)

- `docker-compose up`

or in the background: `docker-compose up -d`

## inside the container

If you want to test things directly inside the container, you can test this commands:

```bash
python inference.py --face /temp/video/1.mp4 --audio /temp/audio/1.wav --outfile /temp/results/1_1.mp4
```

You can also place test files in the temp folder on windows and run the command from the container to test the setup.