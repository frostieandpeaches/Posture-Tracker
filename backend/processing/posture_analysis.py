import os
import math
import cv2
import json
import logging
import mediapipe as mp
from .preprocess import upscale_if_needed
import subprocess

logging.basicConfig(level=logging.INFO)
mp_pose = mp.solutions.pose

def analyze_posture(video_path, file_id):
    try:
        uploads_dir = os.path.join('/app/uploads')
        results_dir = os.path.join('/app/results')
       
        os.makedirs(results_dir, exist_ok=True)

        input_video_path = os.path.join(uploads_dir, os.path.basename(video_path))
        result_video_path = os.path.join(results_dir, f"{file_id}_overlay.mp4")
        result_json_path = os.path.join(results_dir, f"{file_id}.json")

        logging.info(f"Analyzing posture for file: {input_video_path}")

        # Check if video exists
        if not os.path.exists(input_video_path):
            raise FileNotFoundError(f"Video file not found at: {input_video_path}")

        # Optional preprocessing (resize if needed)
        input_video_path = upscale_if_needed(input_video_path)

        cap = cv2.VideoCapture(input_video_path)
        if not cap.isOpened():
            raise RuntimeError(f"Failed to open video: {input_video_path}")

        pose = mp_pose.Pose(static_image_mode=False)
        posture_data = []

        # Video writer setup
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        out = cv2.VideoWriter(result_video_path, fourcc, fps, (width, height))

        frame_count = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame_count += 1
            try:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            except cv2.error as e:
                logging.error(f"cv2.cvtColor failed at frame {frame_count}: {e}")
                break

            results = pose.process(frame_rgb)
            posture_angle = 0  # Default value for frames without detection

            if results.pose_landmarks:
                landmarks = results.pose_landmarks.landmark
                shoulder_y = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y
                hip_y = landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y
                shoulder_x = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x
                hip_x = landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].x
                posture_angle = 90-math.degrees(math.atan2(hip_y - shoulder_y, hip_x - shoulder_x))
                posture_data.append(posture_angle)

                # Draw landmarks for visual overlay
                mp.solutions.drawing_utils.draw_landmarks(
                    frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS
                )

            # Overlay posture angle on the frame
            cv2.putText(
                frame,
                f"Angle: {posture_angle:.2f}",
                (30, 50),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 255, 0),
                2
            )

            out.write(frame)

        cap.release()
        out.release()
        pose.close()
        cv2.destroyAllWindows()


        if posture_data:
            avg_angle = sum(posture_data) / len(posture_data)
        else:
            avg_angle = 0

        results_data = {
            "average_angle": avg_angle,
            "frames_analyzed": len(posture_data)
        }

        with open(result_json_path, "w") as f:
            json.dump(results_data, f, indent=2)

        subprocess.run([
            "ffmpeg", "-y",
            "-i", result_video_path,
            "-c:v", "libx264",
            "-preset", "fast",
            "-pix_fmt", "yuv420p",
            result_video_path.replace(".mp4", "_fixed.mp4")
        ], check=True)

        logging.info(f"✅ Saved results to {result_json_path}")
        logging.info(f"✅ Saved video overlay to {result_video_path}")

        return {
            "status": "complete",
            "average_angle": avg_angle,
            "result_json": result_json_path,
            "video_url": result_video_path
        }

    except Exception as e:
        logging.error(f"❌ Error during posture analysis: {e}")
        return {"status": "error", "message": str(e)}


