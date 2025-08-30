import cv2, time, pickle, base64, queue, threading, redis, logging, traceback
import numpy as np
from storeimages import StoreImage
from config import *

# Configure logging
logging.basicConfig(
    filename="fps_drop.log", level=logging.INFO, format="%(asctime)s - %(message)s"
)

store_images = StoreImage()


class Inference:
    """
    Class for performing inference.
    """

    def __init__(self) -> None:
        """
        Initialize Inference class.
        """
        try:
            self.client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)
            self.pubsub = self.client.pubsub()
            self.pubsub.subscribe(STREAM_TOPIC_GREENCAM2)
            self.image_queue = queue.Queue(maxsize=IMAGE_QUEUE_MAXSIZE)
            self.angle = 0

            self.thread = threading.Thread(target=self.value_pooling, daemon=True)
            self.thread.start()

            self.thread1 = threading.Thread(target=self.start_request, daemon=True)
            self.thread1.start()

        except Exception as e:
            print(f"Error during initialization: {e}")

    def infer_image(self, image, image_id=0):
        """
        Publishes the image data for inference.
        """
        data = {"image": image, "imageId": image_id}
        serialized = pickle.dumps(data)
        try:
            self.client.publish(STREAM_TOPIC_GREENCAM2, serialized)
        except Exception as e:
            print(f"Error publishing image for inference: {e}")
            return {"status": 500}
        data["status"] = 200
        return data

    def check_redis_connection(self):
        """Check if Redis connection is healthy."""
        try:
            if not self.client.ping():
                return False
            if not self.pubsub.connection:
                return False
            return True
        except Exception as e:
            print(f"Redis connection check failed: {e}")
            return False

    def reconnect_redis(self):
        """Reconnect to Redis and re-subscribe to channels."""
        while True:
            try:
                print("Attempting to reconnect to Redis...")
                logging.info("Attempting to reconnect to Redis...")
                
                # Close existing connections
                try:
                    if hasattr(self, 'pubsub') and self.pubsub:
                        self.pubsub.close()
                    if hasattr(self, 'client') and self.client:
                        self.client.close()
                except Exception as e:
                    print(f"Error closing existing connections: {e}")
                
                # Reconnect
                self.client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)
                self.pubsub = self.client.pubsub()
                self.pubsub.subscribe(STREAM_TOPIC_GREENCAM2)
                
                # Test connection and subscription
                if self.client.ping() and self.pubsub.connection:
                    print("Reconnected to Redis successfully and re-subscribed to channels.")
                    logging.info("Reconnected to Redis successfully and re-subscribed to channels.")
                    break
                else:
                    print("Redis connected but subscription failed, retrying...")
                    logging.warning("Redis connected but subscription failed, retrying...")
                    time.sleep(2)
                    
            except Exception as e:
                print(f"Reconnect attempt failed: {e}")
                logging.error(f"Reconnect attempt failed: {e}")
                time.sleep(5)

    def value_pooling(self):
        """
        Continuously pools values from Redis pubsub.
        """
        last_connection_check = time.time()
        while True:
            try:
                # Check connection health every 30 seconds
                if time.time() - last_connection_check > CONNECTION_CHECK_INTERVAL:
                    if not self.check_redis_connection():
                        print("Redis connection lost, attempting reconnection...")
                        logging.warning("Redis connection lost, attempting reconnection...")
                        self.reconnect_redis()
                    last_connection_check = time.time()
                
                data = self.pubsub.get_message()
                if data is None or data["data"] == 1:
                    time.sleep(0.001)
                    continue
                if not self.image_queue.full():
                    try:
                        self.image_queue.put(pickle.loads(data["data"]))
                    except (pickle.PickleError, KeyError, TypeError) as e:
                        print(f"Error unpickling data in value_pooling: {e}")
                        logging.error(f"Error unpickling data in value_pooling: {e}")
                time.sleep(0.001)
            except redis.exceptions.ConnectionError as e:
                print(f"Redis connection error in value_pooling: {e}")
                logging.error(f"Redis connection error in value_pooling: {e}")
                self.reconnect_redis()
            except Exception as e:
                print(f"Error in value pooling: {e}")
                traceback.print_exc()

    def get_infer_result(self):
        """
        Retrieves inference results from the image queue.
        """
        try:
            if not self.image_queue.empty():
                return True, self.image_queue.get()
            else:
                return False, ""
        except Exception as e:
            print(f"Error retrieving inference result: {e}")

    def decode_image(self, encoded_string):
        """
        Decodes base64 encoded image string.
        """
        try:
            encoded_image = base64.decodebytes(encoded_string.encode("utf-8"))
            decoded_image = cv2.imdecode(np.frombuffer(encoded_image, np.uint8), 1)
            return decoded_image
        except Exception as e:
            print(f"Error decoding image: {e}")
            return None
    
    def send_request(self,angle):
        """Infer image."""
        data = {}
        data["angle"] = angle
        serialized = pickle.dumps(data)
        try:
            self.client.publish(REQUEST_TOPIC_GREENCAM2, serialized)
        except Exception as e:
            print(e)
            return {"status": 500}
        data["status"] = 200
        return data

    def start_request(self):
        while True:
            try:
                self.angle = self.angle + 25
                if self.angle > 1000:
                    self.angle = 0
                self.send_request(self.angle)
                time.sleep(REQUEST_INTERVAL)
                
            except Exception as e:
                print(f"Error in value pooling: {e}")
        


cnt = 0
inference = Inference()
start_time = 0
last_connection_check = time.time()

while True:
    try:
        # Check connection health every 30 seconds
        if time.time() - last_connection_check > CONNECTION_CHECK_INTERVAL:
            if not inference.check_redis_connection():
                print("Redis connection lost in main loop, attempting reconnection...")
                logging.warning("Redis connection lost in main loop, attempting reconnection...")
                inference.reconnect_redis()
            last_connection_check = time.time()
        
        ret, output = inference.get_infer_result()
        if ret and output["image"]!="" and output["image"] is not None:
            print(output["image"])
            cnt += 1
            #output["image"] = inference.decode_image(output["image"])
            # output["image"] = cv2.cvtColor(output["image"], cv2.COLOR_BGR2RGB)
            store_images.set_image(output["image"], f"{IMAGES_DIR}/{str(time.time())}.jpg")
            image = output["image"]
            # print(image.shape)
            # cv2.imshow("frame", image)
            # if cv2.waitKey(1) & 0xFF == ord("q"):
            #     break

        # calculate the frame rate
        if time.time() - start_time > 1:
            print("fps: ", cnt)
            if cnt == 0:  # fps dropped to 0
                logging.info("FPS dropped to 0")
            cnt = 0
            start_time = time.time()

        time.sleep(MAIN_LOOP_SLEEP)
    except Exception as e:
        print(f"Error in main loop: {e}")

