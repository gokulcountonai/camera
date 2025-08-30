import os
import psutil
import json
import signal
import redis
import time
import threading
import logging
from logging.handlers import RotatingFileHandler


LOG_FILE = "greencam.log"
MAX_LOG_SIZE = 100 * 1024 * 1024  # 5MB


def setup_logging():
    logging.shutdown()  # Ensure any previous logging is properly shut down
    logger = logging.getLogger()

    # Remove all existing handlers
    while logger.handlers:
        logger.handlers.pop()

    # handler = RotatingFileHandler(LOG_FILE, maxBytes=MAX_LOG_SIZE, backupCount=BACKUP_COUNT)
    handler = RotatingFileHandler(LOG_FILE, maxBytes=MAX_LOG_SIZE, delay=True)
    handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    
    logger.setLevel(logging.INFO)  # Set level before adding handlers
    logger.addHandler(handler)

    handler.flush()  # Ensure logs are written immediately



def check_log_file_exists():
    """Ensure the log file exists. If missing, recreate it."""
    if not os.path.exists(LOG_FILE):
        print(f"⚠️ Warning: Log file {LOG_FILE} is missing! Recreating it...")
        logging.warning("⚠️ Warning: Log file is missing! Recreating it...")

        # Reinitialize logging to recreate the file
        setup_logging()

        # Write an entry to confirm the log is working
        logging.info("✅ Log file recreated successfully.")




        
def kill_python_file(file_name):
    """Terminate Python processes running the specified file.

    Args:
        file_name (str): The name of the Python file to terminate processes for.
    """
    try:
        pids = []
        with os.popen("pgrep -f {}".format(file_name)) as p:
            pids = p.read().splitlines()

        if pids:
            for pid in pids:
                os.kill(int(pid), signal.SIGTERM)
                print(
                    "Process {} (Python file: {}) terminated.".format(
                        pid, file_name
                    )
                )
        else:
            print("No process found for Python file: {}".format(file_name))

        return True

    except Exception as e:
        print(f"Error in Killing python file: {e}")
        check_log_file_exists()
        logging.error(f"Error in Killing python file: {e}")
        return False


def get_cpu_performance():
    """Get the CPU performance."""
    try:
        return psutil.cpu_percent()

    except Exception as e:
        print(f"Error in get_cpu_performance: {e}")
        check_log_file_exists()
        logging.error(f"Error in get_cpu_performance: {e}")
        return None


def get_temperature():
    """Get the temperature."""
    try:
        from gpiozero import CPUTemperature

        cpu_temp = CPUTemperature()
        return cpu_temp.temperature

    except Exception as e:
        print(f"Error in get_temperature: {e}")
        check_log_file_exists()
        logging.error(f"Error in get_temperature: {e}")
        return None


def get_memory_usage():
    """Get the memory usage."""
    try:
        mem = psutil.virtual_memory()
        return mem.percent

    except Exception as e:
        print(f"Error in get_memory_usage: {e}")
        check_log_file_exists()
        logging.error(f"Error in get_memory_usage: {e}")
        return None


def connect_to_redis():
    """Create a Redis client and attempt to connect."""
    try:
        client = redis.Redis(host="169.254.0.1", port=6379, db=0, socket_timeout=5,health_check_interval=5)
        client.ping()  # Test the connection
        return client
    except Exception as e:
        print(f"Error connecting to Redis: {e}")
        check_log_file_exists()
        logging.error(f"Error connecting to Redis: {e}")
        return None


def reconnect_redis():
    """Attempt to reconnect to the Redis server."""
    while True:
        try:
            print("Attempting to reconnect to Redis...")
            check_log_file_exists()
            logging.info("Attempting to reconnect to Redis...")
            client = connect_to_redis()
            if client and client.ping():
                print("Reconnected to Redis successfully.")
                check_log_file_exists()
                logging.info("Reconnected to Redis successfully.")
                logging.info("Rebooting the system...")
                os.system("sudo reboot")
                return client
        except Exception as e:
            print(f"Reconnect attempt failed: {e}")
            check_log_file_exists()
            logging.error(f"Reconnect attempt failed: {e}")
            time.sleep(5)


def sent_log():
    """Continuously log data to Redis."""
    try:
        redis_client = connect_to_redis()

        while True:
            try:
                if redis_client is None or not redis_client.ping():
                    redis_client = reconnect_redis()

                cpu_performance = get_cpu_performance()
                temperature = get_temperature()
                memory_usage = get_memory_usage()

                if None not in [cpu_performance, temperature, memory_usage]:
                    data = [cpu_performance, temperature, memory_usage]
                    try:
                        redis_client.publish("greencam1_log", json.dumps(data))
                        print("data_send", json.dumps(data))
                    except redis.exceptions.ConnectionError as e:
                        print(f"Redis connection error: {e}")
                        check_log_file_exists()
                        logging.error(f"Redis connection error: {e}")
                        redis_client = reconnect_redis()
                    except Exception as e:
                        print(f"Error in publishing log: {str(e)}")
                        check_log_file_exists()
                        logging.error(f"Error in publishing log: {str(e)}")
                # Log data every 5 seconds
                time.sleep(5)

            except Exception as e:
                print(f"Error in inside loop sent_log: {e}")
                check_log_file_exists()
                logging.error(f"Error in inside loop sent_log: {e}")
                reconnect_redis()

    except KeyboardInterrupt:
        print("Logging stopped.")
        check_log_file_exists()
        logging.error("Keyboard Interrupt")

    except Exception as e:
        print(f"Error in sent_log: {e}")
        check_log_file_exists()
        logging.error(f"Error in sent_log: {e}")
        reconnect_redis()


if __name__ == "__main__":
    setup_logging()

    threading.Thread(target=sent_log).start()
    """Check for a kill signal in the 'kill.txt' file and terminate the Python process accordingly."""
    while True:
        try:
            with open("kill.txt", "r+") as f:
                content = f.read().strip()
                if content == "1":
                    kill_python_file("cam1_stream.py")
                    print("File killed successfully")
                    f.seek(0)
                    f.write("0")
                    os.system("sudo python3 cam1_stream.py &")
                    f.truncate()
            time.sleep(1)
            print(content)

        except Exception as e:
            print(f"Error in check_kill_file: {e}")
            check_log_file_exists()
            logging.error(f"Error in check_kill_file: {e}")
