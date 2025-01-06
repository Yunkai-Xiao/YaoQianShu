import tensorflow as tf

# List available devices
physical_devices = tf.config.list_physical_devices('GPU')
print("Num GPUs Available: ", len(physical_devices))

# Check TensorFlow logs for GPU usage
print("Using GPU: ", tf.test.is_gpu_available())
