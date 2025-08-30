import cv2
import time
import queue
import threading
import os
from config import *


class StoreImage:
    def __init__(self):
        self.imageQueue = queue.Queue(maxsize=STORE_QUEUE_MAXSIZE)
        self.thread = threading.Thread(target=self.storeimage, daemon=True)
        self.thread.start()

    def storeimage(self):
        while True:
            try:
                if self.imageQueue.qsize() > 0:
                    image, location = self.imageQueue.get(timeout=1)  # Add timeout to prevent blocking
                    # Ensure directory exists before writing
                    try:
                        os.makedirs(os.path.dirname(location), exist_ok=True)
                        cv2.imwrite(location, image)
                        # Clear image from memory after writing
                        del image
                    except Exception as e:
                        print(f"Error saving image to {location}: {e}")
                else:
                    time.sleep(STORE_SLEEP)
            except queue.Empty:
                # Queue timeout, continue loop
                continue
            except Exception as e:
                print(f"Error in storeimage loop: {e}")
                time.sleep(STORE_SLEEP)

    def set_image(self, image, location):
        self.imageQueue.put([image, location])
        return True

    def setDefectImage(self, image, location):
        self.imageQueue.put([image, location])
        return True
