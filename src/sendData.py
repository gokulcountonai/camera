import os
import threading
import queue
import redis
import pickle
import time
import logging
from config import *

# Configure logging
logging.basicConfig(filename='greencam.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

class Datatransfer:
    """
    Class for transferring data to Redis pubsub.
    """

    def __init__(self, ip, reqtopic, sendtopic):
        """
        Initialize Datatransfer class.
        """
        self.ip = ip
        self.reqtopic = reqtopic
        self.sendtopic = sendtopic
        self.connect_to_redis()

        self.imageQueue = queue.Queue(maxsize=IMAGE_QUEUE_MAXSIZE)
        self.thread1 = threading.Thread(target=self.data_transfer)
        self.thread1.start()

    def connect_to_redis(self):
        """
        Connect to Redis server.
        """
        try:
            self.client = redis.Redis(host=self.ip, port=REDIS_PORT, db=REDIS_DB, socket_timeout=REDIS_TIMEOUT, health_check_interval=REDIS_HEALTH_CHECK_INTERVAL)
            self.p = self.client.pubsub()
            self.p.subscribe(self.reqtopic)
            
            # Test the connection and subscription
            if not self.client.ping():
                raise Exception("Redis ping failed")
            if not self.p.connection:
                raise Exception("Pubsub connection failed")
                
        except Exception as e:
            print(f"Error connecting to Redis: {e}")
            logging.error(f"Error connecting to Redis: {e}")
            raise

    def reconnect_to_redis(self):
        """
        Attempt to reconnect to the Redis server and re-subscribe to channels.
        """
        while True:
            try:
                print("Attempting to reconnect to Redis...")
                logging.info("Attempting to reconnect to Redis...")
                
                # Close existing connections if they exist
                try:
                    if hasattr(self, 'p') and self.p:
                        self.p.close()
                    if hasattr(self, 'client') and self.client:
                        self.client.close()
                except Exception as e:
                    print(f"Error closing existing connections: {e}")
                
                # Reconnect and re-subscribe
                self.connect_to_redis()
                
                # Test the connection and subscription
                if self.client.ping():
                    # Verify subscription is working by checking pubsub
                    if self.p and self.p.connection:
                        print("Reconnected to Redis successfully and re-subscribed to channels.")
                        logging.info("Reconnected to Redis successfully and re-subscribed to channels.")
                        break
                    else:
                        print("Redis connected but pubsub subscription failed, retrying...")
                        logging.warning("Redis connected but pubsub subscription failed, retrying...")
                        time.sleep(2)
                else:
                    print("Redis ping failed, retrying...")
                    logging.warning("Redis ping failed, retrying...")
                    time.sleep(2)
                    
            except Exception as e:
                print(f"Reconnect attempt failed: {e}")
                logging.error(f"Reconnect attempt failed: {e}")
                time.sleep(5)

    def send_data(self, image, status=False, **extra_data):
        """
        Sends data to the image queue, dynamically handling extra fields.
        """
        try:
            if not self.imageQueue.full():
                message = {"image": image, "status": status, **extra_data}  # Merge extra fields
                self.imageQueue.put(message)
                return True
            else:
                return False
        except Exception as e:
            print(f"Error sending data: {e}")
            logging.error(f"Error sending data: {e}")
            return False


    def data_transfer(self):
        """
        Transfers data from the image queue to Redis pubsub.
        """
        while True:
            try:
                time.sleep(0.0005)

                if not self.imageQueue.empty():
                    instance = self.imageQueue.get()
                    serialized = pickle.dumps(instance)
                    try:
                        self.client.publish(self.sendtopic, serialized)
                    except redis.exceptions.ConnectionError as e:
                        print(f"Redis connection error: {e}")
                        logging.error(f"Redis connection error: {e}")
                        self.reconnect_to_redis()
                    except Exception as e:
                        print(f"Error publishing image data: {e}")
                        logging.error(f"Error publishing image data: {e}")
                        self.reconnect_to_redis()
                    instance["status"] = 200
            except Exception as e:
                print(f"Error in data transfer: {e}")
                logging.error(f"Error in data transfer: {e}")

# Example usage:
# dt = Datatransfer(ip='127.0.0.1', reqtopic='request', sendtopic='response')
# dt.send_data(image_data)
