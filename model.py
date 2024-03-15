import keras
import tensorflow as tf
from keras import layers
from keras.layers import Conv2D, GlobalMaxPooling2D, Activation, MaxPooling2D, Dropout, Flatten, Dense
from keras.applications import VGG19

tf.experimental.numpy.experimental_enable_numpy_behavior()
tf.compat.v1.enable_eager_execution()

batch_size = 64
img_h = 256
img_w = 256
epochs = 15
classes = ["bedframe", "chair", "coffee_tables", "desks", "dining_tables", "dressers", "lamps", "nightstand", "ottoman", "shelves", "sofas"]

train_ds, val_ds = keras.utils.image_dataset_from_directory(
    directory=r"data\bedframe",
    validation_split=0.2,
    subset="both",
    seed=123,
    image_size=(img_h, img_w),
    batch_size=batch_size,
)

class_names = train_ds.class_names
num_classes = len(class_names)

data_augmentation = keras.Sequential([
    layers.RandomRotation(0.3),
    layers.RandomZoom(0.3),
    layers.RandomFlip("horizontal"),
    layers.RandomTranslation(height_factor=0.1, width_factor=0.1),
    layers.RandomContrast(0.25),
])

AUTOTUNE = tf.data.AUTOTUNE

def preprocess_data(image, label): 
    image = tf.image.convert_image_dtype(image, tf.float32)
    image = tf.image.resize(image, (img_h, img_w)) 
    return image, label

train_ds = train_ds.map(preprocess_data, num_parallel_calls=AUTOTUNE)
train_ds = train_ds.map(lambda x, y: (data_augmentation(x, training=True), y), num_parallel_calls=AUTOTUNE)
train_ds = train_ds.prefetch(buffer_size=AUTOTUNE)

val_ds = val_ds.map(preprocess_data, num_parallel_calls=AUTOTUNE)
val_ds = val_ds.prefetch(buffer_size=AUTOTUNE)

base_model = VGG19(weights='imagenet', include_top=False, input_shape=(img_h, img_w, 3))
base_model.trainable = False

model = keras.Sequential([
    base_model,
    Conv2D(32, kernel_size=(3, 3), padding='same'),
    Activation('relu'),
    Conv2D(32, kernel_size=(3, 3)),
    Activation('relu'),
    MaxPooling2D(pool_size=(2,2)),
    Dropout(0.25),

    Conv2D(64, kernel_size=(3, 3), padding='same'),
    Activation('relu'),
    Conv2D(64,kernel_size=(3, 3)),
    Activation('relu'),
    GlobalMaxPooling2D(),
    Dropout(0.25),

    Flatten(),
    Dense(256, kernel_regularizer=keras.regularizers.l2(0.001)),
    Dropout(0.5),
    Dense(num_classes, kernel_regularizer=keras.regularizers.l2(0.001))
])

early_stopping = keras.callbacks.EarlyStopping(
    monitor='val_loss', 
    patience=4, 
    restore_best_weights=True,
)

for images, labels in train_ds.take(batch_size):
    sample_images = images.numpy()
    sample_labels = labels.numpy()

w = tf.summary.create_file_writer('logs')

tb_callback = keras.callbacks.TensorBoard('./logs', update_freq=1)
#cm_callback = keras.callbacks.LambdaCallback(on_epoch_end=cm.log_confusion_matrix(epochs, model, sample_images, sample_labels, classes, w)) 

initial_learning_rate = 0.001
decay_steps = 1000
decay_rate = 0.95

lr_schedule = keras.optimizers.schedules.ExponentialDecay(
    initial_learning_rate=initial_learning_rate,
    decay_steps=decay_steps,
    decay_rate=decay_rate,
    staircase=True
)

model.compile(
    optimizer=keras.optimizers.Adam(learning_rate=lr_schedule),
    loss=keras.losses.SparseCategoricalCrossentropy(from_logits=True),
    metrics=['accuracy']
)

history = model.fit(
    train_ds,
    epochs=epochs,
    validation_data=val_ds,
    callbacks=[tb_callback], #, cm_callback],
    verbose=1
)
