"""
Configuration file for the camera streaming system.
Centralizes all settings to make the code more maintainable.
"""

# Redis Configuration
REDIS_HOST = "169.254.0.1"
REDIS_PORT = 6379
REDIS_DB = 0
REDIS_TIMEOUT = 5
REDIS_HEALTH_CHECK_INTERVAL = 5

# Topics
REQUEST_TOPIC_GREENCAM1 = "request/greencam1"
REQUEST_TOPIC_GREENCAM2 = "request/greencam2"
STREAM_TOPIC_GREENCAM1 = "stream/greencam1"
STREAM_TOPIC_GREENCAM2 = "stream/greencam2"
LOG_TOPIC = "greencam1_log"

# Logging Configuration
LOG_FILE = "greencam.log"
MAX_LOG_SIZE = 100 * 1024 * 1024  # 100MB
BACKUP_COUNT = 3

# Camera Configuration
CAMERA_WIDTH = 1270
CAMERA_HEIGHT = 720
CAMERA_FORMAT = "RGB888"
EXPOSURE_TIME = 250
ANALOGUE_GAIN = 3.0
FRAME_RATE = 100

# Threading Configuration
IMAGE_QUEUE_MAXSIZE = 10
STORE_QUEUE_MAXSIZE = 1000

# Timing Configuration
REQUEST_INTERVAL = 0.100  # seconds
LOG_INTERVAL = 5  # seconds
THREAD_TIMEOUT = 1  # seconds
MAIN_LOOP_SLEEP = 0.005  # seconds
STORE_SLEEP = 0.01  # seconds

# File Paths
IMAGES_DIR = "./images"
KILL_FILE = "kill.txt"

# System Configuration
REBOOT_COMMAND = "sudo reboot"
PYTHON_COMMAND = "sudo python3"