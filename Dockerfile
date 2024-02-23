# Windows only
#
# Before building this Dockerfile, ensure you have NVIDIA Docker support (nvidia-container-toolkit) installed if you're planning on using GPU acceleration. This setup is required to allow Docker containers to access the host GPU.
# see https://github.com/NVIDIA/nvidia-container-toolkit
#
# You need WSL installed and your linux distro needs to have the nvidia container toolkit installed.
# see https://docs.microsoft.com/en-us/windows/wsl/tutorials/wsl-containers
# https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html

# Use an NVIDIA CUDA image with Conda
FROM nvidia/cuda:12.2.2-cudnn8-devel-ubuntu22.04

# Set a fixed model cache location and non-interactive installation for tzdata
ENV TORCH_HOME=/root/.cache/torch/hub \
    DEBIAN_FRONTEND=noninteractive \
    TZ=America/Los_Angeles

# Set a fixed model cache location.
ENV TORCH_HOME=/root/.cache/torch/hub

# Install basic dependencies
RUN apt-get update && apt-get install -y \
    git \
    ffmpeg \
    wget \
    cmake \
    build-essential \
    libopenblas-dev \
    liblapack-dev \
    && rm -rf /var/lib/apt/lists/* \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime \
    && echo $TZ > /etc/timezone

# Install Miniconda
RUN wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda.sh \
    && bash ~/miniconda.sh -b -p /miniconda \
    && rm ~/miniconda.sh

# Initialize Conda in bash shell, adjust this if using a different shell
RUN /miniconda/bin/conda init bash

# Make non-interactive shell always use conda
ENV PATH=/miniconda/bin:${PATH}

# Create the environment
RUN conda create -y -n video_retalking python=3.8

# Activate the environment by adjusting PATH
ENV PATH=/miniconda/envs/video_retalking/bin:${PATH}

# Clone the project repository
RUN git clone https://github.com/vinthony/video-retalking.git /video-retalking

# Change working directory
WORKDIR /video-retalking

# Copy the requirements file first to leverage Docker cache
COPY requirements.txt /video-retalking/

# Install dependencies
RUN pip install -r requirements.txt \
    && pip install torch==1.9.0+cu111 torchvision==0.10.0+cu111 -f https://download.pytorch.org/whl/torch_stable.html \
    && pip install gradio

# Copy webUI.py from the local folder to /video-retalking in the container
COPY webUI.py /video-retalking/

# disable gradio's telemetry
ENV GRADIO_ANALYTICS_ENABLED=false

# Expose the port the web app will run on
EXPOSE 7860

CMD ["sh", "-c", "echo 'Starting container...'; python -u /video-retalking/webUI.py"]
