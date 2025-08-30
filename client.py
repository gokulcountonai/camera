import cv2, time, pickle, base64, queue, threading, redis, logging, traceback
import numpy as np
from storeimages import StoreImage

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
            self.client = redis.Redis(host="192.254.0.1", port=6379, db=0)
            self.pubsub = self.client.pubsub()
            self.pubsub.subscribe("stream/greencam2")
            self.image_queue = queue.Queue(maxsize=10)
            self.angle = 0

            self.thread = threading.Thread(target=self.value_pooling)
            self.thread.start()

            self.thread1 = threading.Thread(target=self.start_request)
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
            self.client.publish("stream/greencam2", serialized)
        except Exception as e:
            print(f"Error publishing image for inference: {e}")
            return {"status": 500}
        data["status"] = 200
        return data

    def value_pooling(self):
        """
        Continuously pools values from Redis pubsub.
        """
        while True:
            try:
                data = self.pubsub.get_message()
                if data is None or data["data"] == 1:
                    time.sleep(0.001)
                    continue
                if not self.image_queue.full():
                    self.image_queue.put(pickle.loads(data["data"]))
                time.sleep(0.001)
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
            self.client.publish('request/greencam2', serialized)
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
                time.sleep(0.100)
                
            except Exception as e:
                print(f"Error in value pooling: {e}")
        


cnt = 0
inference = Inference()
tT = 0
while True:
    try:
        ret, output = inference.get_infer_result()
        if ret and output["image"]!="" and output["image"] is not None:
            print(output["image"])
            cnt += 1
            #output["image"] = inference.decode_image(output["image"])
            # output["image"] = cv2.cvtColor(output["image"], cv2.COLOR_BGR2RGB)
            store_images.set_image(output["image"], "./images/" + str(time.time()) + ".jpg")
            image = output["image"]
            # print(image.shape)
            # cv2.imshow("frame", image)
            # if cv2.waitKey(1) & 0xFF == ord("q"):
            #     break

        # calculate the frame rate
        if time.time() - tT > 1:
            print("fps: ", cnt)
            if cnt == 0:  # fps dropped to 0
                logging.info("FPS dropped to 0")
            cnt = 0
            tT = time.time()

        time.sleep(0.005)
    except Exception as e:
        print(f"Error in main loop: {e}")

