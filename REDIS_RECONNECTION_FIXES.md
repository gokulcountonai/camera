# Redis Reconnection Fixes

## Problem Description

When the Redis server restarts or the system hosting Redis restarts, the code would successfully reconnect to Redis but fail to receive messages from the subscribed channels. This happened because:

1. **Lost PubSub Subscriptions**: When Redis restarts, all active pubsub subscriptions are lost
2. **Incomplete Reconnection Logic**: The original code only reconnected the Redis client but didn't re-establish pubsub subscriptions
3. **No Connection Health Monitoring**: The code didn't actively monitor connection health to detect disconnections early

## Root Cause Analysis

### Original Issues:
1. **Missing PubSub Re-subscription**: After Redis restart, pubsub channels weren't re-subscribed
2. **No Connection Cleanup**: Old connections weren't properly closed before creating new ones
3. **Insufficient Error Handling**: Connection errors weren't properly caught and handled
4. **No Health Checks**: No periodic verification that connections and subscriptions were still active

## Solutions Implemented

### 1. Enhanced Reconnection Logic

#### In `src/sendData.py`:
- **Added connection cleanup**: Close existing connections before creating new ones
- **Enhanced subscription verification**: Verify both Redis connection and pubsub subscription are working
- **Improved error handling**: Better exception handling with specific error messages

```python
def reconnect_to_redis(self):
    """Attempt to reconnect to the Redis server and re-subscribe to channels."""
    while True:
        try:
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
                if self.p and self.p.connection:
                    print("Reconnected to Redis successfully and re-subscribed to channels.")
                    break
                else:
                    print("Redis connected but pubsub subscription failed, retrying...")
                    time.sleep(2)
```

#### In `cam1_stream.py`:
- **Dual client reconnection**: Handle both the main Redis client and the Datatransfer client
- **Subscription verification**: Ensure both clients have working pubsub subscriptions
- **Comprehensive health checks**: Verify all connection components are functional

### 2. Connection Health Monitoring

#### Added `check_redis_connection()` methods:
- **Periodic health checks**: Check connection health every 30 seconds (configurable)
- **Comprehensive verification**: Test both Redis ping and pubsub connection status
- **Early detection**: Detect connection issues before they cause message loss

```python
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
```

### 3. Enhanced Error Handling

#### Added specific exception handling:
- **Redis connection errors**: Catch `redis.exceptions.ConnectionError` specifically
- **Pubsub errors**: Handle pubsub-specific connection issues
- **Graceful degradation**: Continue operation while attempting reconnection

### 4. Configuration Improvements

#### Added to `config.py`:
```python
CONNECTION_CHECK_INTERVAL = 30  # seconds - How often to check Redis connection health
```

## Files Modified

### 1. `src/sendData.py`
- Enhanced `reconnect_to_redis()` method
- Added connection cleanup
- Improved subscription verification
- Better error handling

### 2. `cam1_stream.py`
- Enhanced `reconnect_redis()` method
- Added `check_redis_connection()` method
- Added periodic connection health monitoring
- Improved dual-client reconnection logic

### 3. `start.py`
- Enhanced `reconnect_redis()` method
- Added connection cleanup
- Improved error handling

### 4. `client.py`
- Added `check_redis_connection()` method
- Added `reconnect_redis()` method
- Enhanced `value_pooling()` with connection monitoring
- Added connection health checks in main loop

### 5. `config.py`
- Added `CONNECTION_CHECK_INTERVAL` configuration

## Key Improvements

### 1. **Automatic Re-subscription**
- When Redis restarts, all pubsub subscriptions are automatically re-established
- No manual intervention required

### 2. **Proactive Health Monitoring**
- Connection health is checked every 30 seconds
- Issues are detected before they cause message loss

### 3. **Robust Error Recovery**
- Multiple layers of error handling
- Graceful degradation during connection issues

### 4. **Comprehensive Logging**
- Detailed logging of connection events
- Better debugging information

### 5. **Configurable Parameters**
- Connection check intervals can be adjusted via configuration
- Easy to tune for different environments

## Testing Recommendations

### 1. **Redis Restart Test**
1. Start the application
2. Restart Redis server
3. Verify that messages are received after reconnection
4. Check logs for reconnection messages

### 2. **Network Interruption Test**
1. Start the application
2. Temporarily block network access to Redis
3. Restore network access
4. Verify automatic reconnection and message reception

### 3. **Long-running Stability Test**
1. Run the application for extended periods
2. Monitor for connection drops and recoveries
3. Verify message continuity

## Expected Behavior

### Before Fix:
- Redis restart → Connection successful but no messages received
- Network interruption → Manual restart required
- Connection drops → Silent failures

### After Fix:
- Redis restart → Automatic reconnection and re-subscription
- Network interruption → Automatic recovery
- Connection drops → Proactive detection and recovery

## Monitoring and Debugging

### Log Messages to Watch For:
- `"Attempting to reconnect to Redis..."`
- `"Reconnected to Redis successfully and re-subscribed to channels."`
- `"Redis connection lost, attempting reconnection..."`
- `"Redis connected but pubsub subscription failed, retrying..."`

### Configuration Tuning:
- Adjust `CONNECTION_CHECK_INTERVAL` based on your environment
- Monitor connection frequency in logs
- Tune reconnection retry intervals if needed