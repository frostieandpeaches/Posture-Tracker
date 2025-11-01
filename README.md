Posture App
Overview

A web app that tracks a user’s posture in real time and gives alerts when slouching is detected.

Features

Real-time body tracking using Mediapipe.

Frontend built with React and FastAPI backend.

Worker queue using Redis for asynchronous tasks.

Containerized with Docker for isolated testing.

System Architecture

The project uses a modular client–server architecture designed for scalability and responsiveness.

Frontend: Built with Vite, responsible for obtaining video input and sending frames to the backend via REST API calls.

Backend: Developed using FastAPI. Handles video upload, request routing, and job distribution.

Processing Queue: Redis manages a worker queue to prevent overload and maintain consistent response times. Each frame request is queued, processed asynchronously, and results are returned once complete.

Model Inference: The posture detection uses Mediapipe’s pre-trained model for pose tracking. The backend processes each frame, extracts key landmarks, and computes posture feedback.

Containerization: Docker is used to isolate the backend and worker environments, ensuring consistent performance across systems.

Deployment: The app can be deployed locally or in a cloud environment with minimal configuration.

Setup

1. Clone the repository.

2. Run docker-compose up to start the app and queue system.

3. Access the app in your browser at localhost:5173.

Technologies

FastAPI, React, Redis, Docker, Mediapipe
