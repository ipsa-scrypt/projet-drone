import csv
import math
import os
import queue
import shlex
import subprocess
import tempfile
import threading
import time
import pygame
import cv2
import matplotlib.pyplot as plt
import cv2
import argparse

from ultralytics import YOLO
import supervision as sv

try:
    import olympe
    from olympe.messages.ardrone3.Piloting import TakeOff, Landing, moveBy, CancelMoveBy
    from olympe.video.renderer import PdrawRenderer
except ImportError as e:
    print(e)
    exit(1)

olympe.log.update_config({"loggers": {"olympe": {"level": "WARNING"}}})

#DRONE_IP = os.environ.get("DRONE_IP", "10.202.0.1")
DRONE_IP = os.environ.get("DRONE_IP", "192.168.42.1")

DRONE_RTSP_PORT = os.environ.get("DRONE_RTSP_PORT")


class StreamingExample:
    def __init__(self):
        # Create the olympe.Drone object from its IP address
        self.drone = olympe.Drone(DRONE_IP)
        self.tempd = tempfile.mkdtemp(prefix="olympe_streaming_test_")
        print(f"Olympe streaming example output dir: {self.tempd}")
        self.h264_frame_stats = []
        self.h264_stats_file = open(os.path.join(self.tempd, "h264_stats.csv"), "w+")
        self.h264_stats_writer = csv.DictWriter(
            self.h264_stats_file, ["fps", "bitrate"]
        )
        self.h264_stats_writer.writeheader()
        self.frame_queue = queue.Queue()
        self.processing_thread = threading.Thread(target=self.yuv_frame_processing)
        self.renderer = None

    def start(self):
        # Connect to drone
        assert self.drone.connect(retry=3)

        if DRONE_RTSP_PORT is not None:
            self.drone.streaming.server_addr = f"{DRONE_IP}:{DRONE_RTSP_PORT}"

        chemin_specifique = "/home/armarit/Documents/Projet_drone/video_drone"

        self.drone.streaming.set_output_files(
            video=os.path.join(chemin_specifique, "streaming.mp4"),
            #metadata=os.path.join(chemin_specifique, "streaming_metadata.json"),
        )
        
        '''
        # You can record the video stream from the drone if you plan to do some
        # post processing.
        self.drone.streaming.set_output_files(
            video=os.path.join(self.tempd, "streaming.mp4"),
            metadata=os.path.join(self.tempd, "streaming_metadata.json"),
        )
        '''

        # Setup your callback functions to do some live video processing
        self.drone.streaming.set_callbacks(
            raw_cb=self.yuv_frame_cb,
            h264_cb=self.h264_frame_cb,
            start_cb=self.start_cb,
            end_cb=self.end_cb,
            flush_raw_cb=self.flush_cb,
        )
        # Start video streaming
        self.drone.streaming.start()
        self.renderer = PdrawRenderer(pdraw=self.drone.streaming)
        self.running = True
        self.processing_thread.start()

    def stop(self):
        self.running = False
        self.processing_thread.join()
        if self.renderer is not None:
            self.renderer.stop()
        # Properly stop the video stream and disconnect
        assert self.drone.streaming.stop()
        assert self.drone.disconnect()
        self.h264_stats_file.close()

    def yuv_frame_cb(self, yuv_frame):
        """
        This function will be called by Olympe for each decoded YUV frame.

            :type yuv_frame: olympe.VideoFrame
        """
        yuv_frame.ref()
        self.frame_queue.put_nowait(yuv_frame)

    def yuv_frame_processing(self):
        #model = YOLO("yolov8l.pt")  # Chargez le modèle une seule fois
        model = YOLO("best.pt")
        bounding_box_annotator = sv.BoundingBoxAnnotator()
        label_annotator = sv.LabelAnnotator()

        while self.running:
            try:
                yuv_frame = self.frame_queue.get(timeout=0.1)
            except queue.Empty:
                continue

            # Convertissez yuv_frame (olympe.VideoFrame) en tableau NumPy, puis en format BGR pour OpenCV

            os.environ['YOLO_VERBOSE'] = 'False'
            
            yuv_data = yuv_frame.as_ndarray()
            bgr_frame = cv2.cvtColor(yuv_data, cv2.COLOR_YUV2BGR_I420)  # Assurez-vous du format YUV correct
            
            bgr_frame = cv2.resize(bgr_frame, (640, 360))  # Ajuster frames
            
            result = model(bgr_frame, verbose=False)[0] #retirer verbose si on veut print console
            detections = sv.Detections.from_ultralytics(result)
            
            labels = [
                f"{det[-1]['class_name']}: {det[2]*100:.2f}%"  # Access 'class_name' key and confidence directly
                for det in detections
            ]
            
            bgr_frame = bounding_box_annotator.annotate(scene=bgr_frame, detections=detections)
            bgr_frame = label_annotator.annotate(scene=bgr_frame, detections=detections, labels=labels)

            cv2.imshow("yolov8", bgr_frame)
        
            if cv2.waitKey(1) & 0xFF == ord('q'):  # q key to break
                break

            yuv_frame.unref() #je sais pas ce que ça fait <scrypt> sinon bah le drone decole plus

        cv2.destroyAllWindows()  # Fermez toutes les fenêtres OpenCV une fois terminé


    
    def flush_cb(self, stream):
        if stream["vdef_format"] != olympe.VDEF_I420:
            return True
        while not self.frame_queue.empty():
            self.frame_queue.get_nowait().unref()
        return True

    def start_cb(self):
        pass

    def end_cb(self):
        pass

    def h264_frame_cb(self, h264_frame):
        """
        This function will be called by Olympe for each new h264 frame.

            :type yuv_frame: olympe.VideoFrame
        """

        # Get a ctypes pointer and size for this h264 frame
        frame_pointer, frame_size = h264_frame.as_ctypes_pointer()

        # For this example we will just compute some basic video stream stats
        # (bitrate and FPS) but we could choose to resend it over an another
        # interface or to decode it with our preferred hardware decoder..

        # Compute some stats and dump them in a csv file
        info = h264_frame.info()
        frame_ts = info["ntp_raw_timestamp"]
        if not bool(info["is_sync"]):
            while len(self.h264_frame_stats) > 0:
                start_ts, _ = self.h264_frame_stats[0]
                if (start_ts + 1e6) < frame_ts:
                    self.h264_frame_stats.pop(0)
                else:
                    break
            self.h264_frame_stats.append((frame_ts, frame_size))
            h264_fps = len(self.h264_frame_stats)
            h264_bitrate = 8 * sum(map(lambda t: t[1], self.h264_frame_stats))
            self.h264_stats_writer.writerow({"fps": h264_fps, "bitrate": h264_bitrate})

    def show_yuv_frame(self, window_name, yuv_frame):
        # the VideoFrame.info() dictionary contains some useful information
        # such as the video resolution
        info = yuv_frame.info()

        height, width = (  # noqa
            info["raw"]["frame"]["info"]["height"],
            info["raw"]["frame"]["info"]["width"],
        )

        # yuv_frame.vmeta() returns a dictionary that contains additional
        # metadata from the drone (GPS coordinates, battery percentage, ...)

        # convert pdraw YUV flag to OpenCV YUV flag
        import cv2
        cv2_cvt_color_flag = {
            olympe.VDEF_I420: cv2.COLOR_YUV2BGR_I420,
            olympe.VDEF_NV12: cv2.COLOR_YUV2BGR_NV12,
        }[yuv_frame.format()]

    def fly(self):
        assert self.drone(TakeOff()).wait().success()
        #self.monitor_keyboard()

        # Initialize Pygame
        pygame.init()

        # Set up the display
        width, height = 800, 600
        screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("Pygame Example")
        clock = pygame.time.Clock()

        keys_pressed = {
            "forward": False,
            "backward": False,
            "left": False,
            "right": False,
            "up": False,
            "down": False,
            "left_angle": False,
            "right_angle": False
        }

        run = True

        while run:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    run = False

                # Touche pressÃ©e
                elif event.type == pygame.KEYDOWN:
                    print("DOWN: \t", end="")
                    if event.key == pygame.K_p:
                        self.emergency()
                        run = False
                    if event.key == pygame.K_UP:
                        keys_pressed["forward"] = True
                        self.forward()
                    if event.key == pygame.K_DOWN:
                        keys_pressed["backward"] = True
                        self.backward()
                    if event.key == pygame.K_LEFT:
                        keys_pressed["left"] = True
                        self.left()
                    if event.key == pygame.K_RIGHT:
                        keys_pressed["right"] = True
                        self.right()
                    if event.key == pygame.K_SPACE:
                        keys_pressed["up"] = True
                        self.up()
                    if event.key == pygame.K_c:
                        keys_pressed["down"] = True
                        self.down()
                    if event.key == pygame.K_b:
                        keys_pressed["left_angle"] = True
                        self.left_angle()
                    if event.key == pygame.K_n:
                        keys_pressed["right_angle"] = True
                        self.right_angle()
                    if event.key == pygame.K_e:
                        self.yuv_frame_processing()

                elif event.type == pygame.KEYUP:
                    print("UP: \t", end="")
                    if event.key == pygame.K_UP:
                        keys_pressed["forward"] = False
                        self.forward()
                    if event.key == pygame.K_DOWN:
                        keys_pressed["backward"] = False
                        self.backward()
                    if event.key == pygame.K_LEFT:
                        keys_pressed["left"] = False
                        self.left()
                    if event.key == pygame.K_RIGHT:
                        keys_pressed["right"] = False
                        self.right()
                    if event.key == pygame.K_SPACE:
                        keys_pressed["up"] = False
                        self.up()
                    if event.key == pygame.K_c:
                        keys_pressed["down"] = False
                        self.down()
                    if event.key == pygame.K_b:
                        keys_pressed["left_angle"] = False
                        self.left_angle()
                    if event.key == pygame.K_n:
                        keys_pressed["right_angle"] = False
                        self.right_angle()

            # Stop si rien n'est fait
            if True not in keys_pressed.values():
                #print("Stop")
                self.stop()

            # Add a clock to control the frame rate
            clock.tick(10)

            # Add code to update the display
            pygame.display.flip()

        pygame.quit()

        assert self.drone(Landing()).wait().success()

    def replay_with_vlc(self):
        # Replay this MP4 video file using VLC
        mp4_filepath = os.path.join(self.tempd, "streaming.mp4")
        subprocess.run(shlex.split(f"vlc --play-and-exit {mp4_filepath}"), check=True)

    def emergency(self):
        try:
            self.drone(Landing()).wait().success()
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            self.drone.disconnect()

    def forward(self):
        print("avancer")
        self.drone(moveBy(1, 0, 0, 0))

    def backward(self):
        print("reculer")
        self.drone(moveBy(-1, 0, 0, 0))

    def right(self):
        print("droite")
        self.drone(moveBy(0, 1, 0, 0))

    def left(self):
        print("gauche")
        self.drone(moveBy(0, -1, 0, 0))

    def right_angle(self):
        print("rotation droite")
        self.drone(moveBy(0, 0, 0, 1))

    def left_angle(self):
        print("rotation gauche")
        self.drone(moveBy(0, 0, 0, -1))

    def up(self):
        print("monter")
        self.drone(moveBy(0, 0, -0.5, 0))

    def down(self):
        print("descendre")
        self.drone(moveBy(0, 0, 0.5, 0))

    def stop(self):
        #print("stop")
        self.drone(CancelMoveBy())


def test_streaming():
    streaming_example = StreamingExample()
    # Start the video stream
    streaming_example.start()

    # Perform some live video processing while the drone is flying
    streaming_example.fly()

    # Stop the video stream
    streaming_example.stop()

    # Recorded video stream postprocessing
    # streaming_example.replay_with_vlc()


if __name__ == "__main__":
    test_streaming()


