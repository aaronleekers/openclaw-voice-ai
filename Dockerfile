# Use PyTorch CUDA base image
FROM pytorch/pytorch:2.1.0-cuda11.8-cudnn8-runtime

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    wget \
    libsndfile1 \
    espeak \
    espeak-data \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies with CORRECT versions
RUN pip install --no-cache-dir \
    torch==2.1.0 \
    torchaudio==2.1.0 \
    TTS==0.22.0 \
    flask==3.0.0 \
    flask-cors==4.0.0 \
    "transformers==4.35.0" \
    "librosa==0.10.1" \
    "pandas<2.0" \
    numpy==1.24.3 \
    soundfile \
    pydub

# Copy server files
COPY server_docker.py /app/server.py
COPY index.html /app/index.html

# Create voices directory
RUN mkdir -p /app/voices

# Expose port
EXPOSE 5000

# Run server
CMD ["python", "server.py"]
