import cv2
import time
import queue
import threading


class StoreImage:
    def __init__(self):
        self.imageQueue = queue.Queue(maxsize=1000)
        self.thread = threading.Thread(target=self.storeimage)
        self.thread.start()

    def storeimage(self):
        while True:
            if self.imageQueue.qsize() > 0:
                image, location = self.imageQueue.get()
                # print("image", image)
                cv2.imwrite(location, image)
            else:
                time.sleep(0.01)

    def set_image(self, image, location):
        self.imageQueue.put([image, location])
        return True

    def setDefectImage(self, image, location):
        self.imageQueue.put([image, location])
        return True
