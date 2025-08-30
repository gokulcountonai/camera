import time,os
import cv2
import base64,traceback
import redis , pickle
from picamera2 import Picamera2
from src.sendData import Datatransfer
import threading,logging
from logging.handlers import RotatingFileHandler
from config import *



# Configuration is now imported from config.py


def setup_logging():
    """Setup logging with RotatingFileHandler."""
    logging.shutdown()  # Ensure previous logging is properly shut down
    logger = logging.getLogger()

    # Remove all existing handlers to avoid duplication
    while logger.handlers:
        logger.handlers.pop()

    # Ensure the log file exists before setting up logging
    if not os.path.exists(LOG_FILE):
        open(LOG_FILE, 'w').close()  # Create an empty file

    # Setup RotatingFileHandler without delay
    handler = RotatingFileHandler(LOG_FILE, maxBytes=MAX_LOG_SIZE, backupCount=3, delay=False)
    handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

    logger.setLevel(logging.INFO)  # Set level before adding handlers
    logger.addHandler(handler)

    handler.flush()  # Ensure logs are written immediately
    logging.info("✅ Logging initialized successfully.")

setup_logging()  # Initialize logging at the start

def check_log_file_exists():
    """Ensure the log file exists. If missing, recreate it."""
    if not os.path.exists(LOG_FILE):
        # print(f"⚠️ Warning: Log file {LOG_FILE} is missing! Recreating it...")

        # Reinitialize logging first, then log the warning
        setup_logging()
        # logging.warning("⚠️ Warning: Log file was missing! Recreated successfully.")



class CameraStreamer:
    """Controls the camera settings and data transfer."""

    def __init__(self,ip,reqtopic,sendtopic):
        """Initialize the CameraStreamer."""
        try:
            self.ip = ip
            self.reqtopic = reqtopic
            self.sendtopic = sendtopic
            self.status = False
            self.image = ""

            self.initialize_camera()
            self.initialize_other_components()
            self.main()
        except Exception as e:
            print(f"Error initializing CameraStreamer: {e}")
            check_log_file_exists()
            logging.error(f"Error initializing CameraStreamer: {e}")
            traceback.print_exc()
        
    def initialize_camera(self):
        """Initialize the camera."""
        try:
            self.camera = Picamera2()
            self.config = self.camera.create_preview_configuration(
                queue=False, main={"size": (CAMERA_WIDTH, CAMERA_HEIGHT), "format": CAMERA_FORMAT}
            )
            self.camera.configure(self.config)
            self.camera.set_controls(
                {"ExposureTime": EXPOSURE_TIME, "AnalogueGain": ANALOGUE_GAIN, "FrameRate": FRAME_RATE}
            )
            self.camera.start()
        except Exception as e:
            print(f"Error initializing camera: {e}")
            check_log_file_exists()
            logging.error(f"Error initializing camera: {e}")
            traceback.print_exc()   

    def initialize_other_components(self):
        """Initialize other components."""
        try:
            self.start_time = time.time()
            self.fps = 0
            self.rec = 599
            self.data_transfer = Datatransfer(self.ip, self.reqtopic, self.sendtopic)

            self.camactivetime = 0
            self.redis_client = redis.Redis(host=self.ip, port=REDIS_PORT, db=REDIS_DB, socket_timeout=REDIS_TIMEOUT, health_check_interval=REDIS_HEALTH_CHECK_INTERVAL)
            self.pubsub_client = self.redis_client.pubsub()
            self.pubsub_client.subscribe(self.reqtopic)
            
            # Test the connection and subscription
            if not self.redis_client.ping():
                raise Exception("Redis ping failed")
            if not self.pubsub_client.connection:
                raise Exception("Pubsub connection failed")
                
        except Exception as e:
            print(f"Error initializing other components: {e}")
            check_log_file_exists()
            logging.error(f"Error initializing other components: {e}")
            traceback.print_exc()

    def reconnect_redis(self):
        """Attempt to reconnect to the Redis server for both clients and re-subscribe to channels."""
        while True:
            try:
                print("Attempting to reconnect to Redis...")
                check_log_file_exists()
                logging.info("Attempting to reconnect to Redis...")

                # Close existing connections if they exist
                try:
                    if hasattr(self, 'pubsub_client') and self.pubsub_client:
                        self.pubsub_client.close()
                    if hasattr(self, 'redis_client') and self.redis_client:
                        self.redis_client.close()
                except Exception as e:
                    print(f"Error closing existing connections: {e}")

                # Reconnect the Datatransfer client
                self.data_transfer.reconnect_to_redis()
                
                # Reconnect the local redis_client and re-subscribe
                self.redis_client = redis.Redis(host=self.ip, port=REDIS_PORT, db=REDIS_DB, socket_timeout=REDIS_TIMEOUT, health_check_interval=REDIS_HEALTH_CHECK_INTERVAL)
                self.pubsub_client = self.redis_client.pubsub()
                self.pubsub_client.subscribe(self.reqtopic)
                
                # Test both connections and subscriptions
                if self.data_transfer.client.ping() and self.redis_client.ping():
                    # Verify pubsub subscription is working
                    if self.pubsub_client and self.pubsub_client.connection:
                        print("Reconnected to Redis successfully for both clients and re-subscribed to channels.")
                        check_log_file_exists()
                        logging.info("Reconnected to Redis successfully for both clients and re-subscribed to channels.")
                        break
                    else:
                        print("Redis connected but pubsub subscription failed, retrying...")
                        check_log_file_exists()
                        logging.warning("Redis connected but pubsub subscription failed, retrying...")
                        time.sleep(2)
                else:
                    print("Redis ping failed for one or both clients, retrying...")
                    check_log_file_exists()
                    logging.warning("Redis ping failed for one or both clients, retrying...")
                    time.sleep(2)
                
            except Exception as e:
                print(f"Reconnect attempt failed: {e}")
                check_log_file_exists()
                logging.error(f"Reconnect attempt failed cam1_stream.py: {e}")
                time.sleep(5)

    def fetch_image(self):
        try:
            array = self.camera.capture_array("main")
            self.status,self.image = True,array

        except Exception as e:
            print(f"Error fetching image: {e}")
            check_log_file_exists()
            logging.error(f"Error fetching image: {e}")
            traceback.print_exc()
            self.status,self.image = False,""
 
    def check_redis_connection(self):
        """Check if Redis connections are healthy."""
        try:
            # Check main Redis client
            if not self.redis_client.ping():
                return False
            # Check pubsub connection
            if not self.pubsub_client.connection:
                return False
            # Check data transfer client
            if not self.data_transfer.client.ping():
                return False
            # Check data transfer pubsub
            if not self.data_transfer.p.connection:
                return False
            return True
        except Exception as e:
            print(f"Redis connection check failed: {e}")
            return False

    def main(self):
        """Main function."""
        try:
            count = 0
            st = time.time()
            while True:
                try:
                    if not self.camera:
                        print("Camera is not initialized.")
                        check_log_file_exists()
                        logging.error("Camera is not initialized.")
                        self.initialize_camera()
                    
                    # Check Redis connection health periodically
                    if time.time() - st > CONNECTION_CHECK_INTERVAL:  # Check connection health
                        if not self.check_redis_connection():
                            print("Redis connection lost, attempting reconnection...")
                            check_log_file_exists()
                            logging.warning("Redis connection lost, attempting reconnection...")
                            self.reconnect_redis()
                        st = time.time()
                    
                    data = self.data_transfer.p.get_message()
                    if time.time() - st > 10:
                        print(data)
                        st = time.time()

                    if data and data["data"] != 1 and data is not None and data["channel"].decode("utf-8") == self.reqtopic:
                        try:
                            data = pickle.loads(data["data"])  # Convert received data from bytes to dict
                        except (pickle.PickleError, KeyError, TypeError) as e:
                            print(f"Error unpickling data: {e}")
                            check_log_file_exists()
                            logging.error(f"Error unpickling data: {e}")
                            continue
                        
                        thread = threading.Thread(target=self.fetch_image)
                        thread.daemon = True  # Make thread daemon so it doesn't block program exit
                        thread.start()
                        thread.join(timeout=THREAD_TIMEOUT)
                        if thread.is_alive():
                            self.image = ""
                            self.status = False
                            print("Error in fetching image - thread timed out")
                            # Force cleanup of stuck thread
                            try:
                                thread._stop()
                            except:
                                pass
                        # Thread will be cleaned up automatically when it completes or times out

                        status, image = self.status, self.image
                        if status and image.size > 0:
                            # ✅ Send all received Redis data dynamically
                            ret = self.data_transfer.send_data(image=image, status="True", **data)
                            print(ret)
                        else:
                            self.data_transfer.send_data(image="", status="False")
                            print("Error in fetching image")
                            check_log_file_exists()
                            logging.error("Error in fetching image")
                            print(count)
                            if count > 10:
                                count = 0
                                with open(KILL_FILE, "r+") as f:
                                    content = f.read().strip()
                                    if content == "0":
                                        f.seek(0)
                                        f.write("1")
                                        f.truncate()

                            count += 1

                except redis.exceptions.ConnectionError as e:
                    print(f"Redis connection error in Main cam1_stream.py: {e}")
                    check_log_file_exists()
                    logging.error(f"Redis connection error in Main cam1_stream.py: {e}")
                    traceback.print_exc()
                    self.reconnect_redis()
                    logging.info("Loop get breaked cam1_stream.py")

                except Exception as e:
                    print(f"Error in Main cam1_stream.py: {str(e)}")
                    check_log_file_exists()
                    logging.error(f"Error in Main cam1_stream.py: {str(e)}")
                    traceback.print_exc()
                    self.reconnect_redis()

        except Exception as e:
            print(f"Error in Main final except main: {str(e)}")
            check_log_file_exists()
            logging.error(f"Error in Main final except main: {str(e)}")
            traceback.print_exc()
            with open(KILL_FILE, "r+") as f:
                content = f.read().strip()
                if content == "0":
                    f.seek(0)
                    f.write("1")
                    f.truncate()


if __name__ == "__main__":

    ip = REDIS_HOST
    reqtopic = REQUEST_TOPIC_GREENCAM1
    sendtopic = STREAM_TOPIC_GREENCAM1
    camstream = CameraStreamer(ip, reqtopic, sendtopic)
