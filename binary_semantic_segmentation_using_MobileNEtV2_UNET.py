# -*- coding: utf-8 -*-
"""binary_semantic_segmentation_using_unet.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1i6BimMt-k-dVXc2GM91uSHNGP2UHpofA

https://youtu.be/oBIkr7CAE6g

Binary semantic segmentation using U-Net
Dataset: https://www.epfl.ch/labs/cvlab/data/data-em/
"""

import tensorflow as tf
from tensorflow.keras.utils import normalize
import os
import cv2
from PIL import Image
import numpy as np
from matplotlib import pyplot as plt
from sklearn.preprocessing import MinMaxScaler
from keras.optimizers import Adam
import glob

from google.colab import files
from google.colab import drive
drive.mount('/content/drive')

from google.colab import drive
drive.mount('/content/drive')

image_directory = '/content/drive/MyDrive/Colab Notebooks/CS-541-Deep Learning/CS541-Final Project/Tomato___healthy/Tomato___healthy'
mask_directory = '/content/drive/MyDrive/Colab Notebooks/CS-541-Deep Learning/CS541-Final Project/Tomato___healthy_mask/Tomato___healthy_mask'

SIZE = 256
num_images = 2644

"""Load images and masks in order so they match"""

path1 = "/content/drive/MyDrive/Colab Notebooks/CS-541-Deep Learning/CS541-Final Project/Tomato___healthy/Tomato___healthy/*.JPG"
path2 = "/content/drive/MyDrive/Colab Notebooks/CS-541-Deep Learning/CS541-Final Project/Tomato___healthy/Tomato___healthy/*.jpg"
path3 = "/content/drive/MyDrive/Colab Notebooks/CS-541-Deep Learning/CS541-Final Project/Tomato___healthy/Tomato___healthy*.jpeg"
image_names = [file for path in [path1, path2, path3] for file in glob.glob(path)]

image_names.sort()

image_names_subset = image_names[0:num_images]

images = [cv2.imread(img, 0) for img in image_names_subset]

image_dataset = np.array(images)
image_dataset = np.expand_dims(image_dataset, axis = 3)

"""Read masks the same way. """

path1 = "/content/drive/MyDrive/Colab Notebooks/CS-541-Deep Learning/CS541-Final Project/Tomato___healthy_mask/Tomato___healthy_mask/*.JPG"
path2 = "/content/drive/MyDrive/Colab Notebooks/CS-541-Deep Learning/CS541-Final Project/Tomato___healthy_mask/Tomato___healthy_mask/*.jpg"
path3 = "/content/drive/MyDrive/Colab Notebooks/CS-541-Deep Learning/CS541-Final Project/Tomato___healthy_mask/Tomato___healthy_mask/*.jpeg"
mask_names = [file for path in [path1, path2, path3] for file in glob.glob(path)]
mask_names.sort()
mask_names_subset = mask_names[0:num_images]
masks = [cv2.imread(mask, 0) for mask in mask_names_subset]
mask_dataset = np.array(masks)
mask_dataset = np.expand_dims(mask_dataset, axis = 3)

print("Image data shape is: ", image_dataset.shape)
print("Mask data shape is: ", mask_dataset.shape)
print("Max pixel value in image is: ", image_dataset.max())
print("Labels in the mask are : ", np.unique(mask_dataset))

#scaler = MinMaxScaler()

#test_image_data=scaler.fit_transform(image_dataset_uint8.reshape(-1, image_dataset_uint8.shape[-1])).reshape(image_dataset_uint8.shape)

#Normalize images
image_dataset = image_dataset /255.  #Can also normalize or scale using MinMax scaler
#Do not normalize masks, just rescale to 0 to 1.
mask_dataset = mask_dataset /255.  #PIxel values will be 0 or 1

from sklearn.model_selection import train_test_split
X_train, X_test, y_train, y_test = train_test_split(image_dataset, mask_dataset, test_size = 0.3, random_state = 42)

#Sanity check, view few mages
import random

image_number = random.randint(0, len(X_train)-1)
plt.figure(figsize=(12, 6))
plt.subplot(121)
plt.imshow(X_train[image_number,:,:,0], cmap='gray')
plt.subplot(122)
plt.imshow(y_train[image_number,:,:,0], cmap='gray')
plt.show()

# Building Unet by dividing encoder and decoder into blocks

from keras.models import Model
from keras.layers import Input, Conv2D, MaxPooling2D, UpSampling2D, concatenate, Conv2DTranspose, BatchNormalization, Dropout, Lambda
from keras.optimizers import Adam
from keras.layers import Activation, MaxPool2D, Concatenate


def conv_block(input, num_filters):
    x = Conv2D(num_filters, 3, padding="same")(input)
    x = BatchNormalization()(x)   #Not in the original network. 
    x = Activation("relu")(x)

    x = Conv2D(num_filters, 3, padding="same")(x)
    x = BatchNormalization()(x)  #Not in the original network
    x = Activation("relu")(x)

    return x

#Encoder block: Conv block followed by maxpooling


def encoder_block(input, num_filters):
    x = conv_block(input, num_filters)
    p = MaxPool2D((2, 2))(x)
    return x, p   

#Decoder block
#skip features gets input from encoder for concatenation

def decoder_block(input, skip_features, num_filters):
    x = Conv2DTranspose(num_filters, (2, 2), strides=2, padding="same")(input)
    x = Concatenate()([x, skip_features])
    x = conv_block(x, num_filters)
    return x

#Build Unet using the blocks
def build_unet(input_shape, n_classes):
    inputs = Input(input_shape)

    s1, p1 = encoder_block(inputs, 64)
    s2, p2 = encoder_block(p1, 128)
    s3, p3 = encoder_block(p2, 256)
    s4, p4 = encoder_block(p3, 512)

    b1 = conv_block(p4, 1024) #Bridge

    d1 = decoder_block(b1, s4, 512)
    d2 = decoder_block(d1, s3, 256)
    d3 = decoder_block(d2, s2, 128)
    d4 = decoder_block(d3, s1, 64)

    if n_classes == 1:  #Binary
      activation = 'sigmoid'
    else:
      activation = 'softmax'

    outputs = Conv2D(n_classes, 1, padding="same", activation=activation)(d4)  #Change the activation based on n_classes
    print(activation)

    model = Model(inputs, outputs, name="U-Net")
    return model

IMG_HEIGHT = image_dataset.shape[1]
IMG_WIDTH  = image_dataset.shape[2]
IMG_CHANNELS = image_dataset.shape[3]

input_shape = (IMG_HEIGHT, IMG_WIDTH, IMG_CHANNELS)

model = build_unet(input_shape, n_classes=1)
model.compile(optimizer=Adam(learning_rate = 1e-3), loss='binary_crossentropy', metrics=['accuracy'])
model.summary()

import tensorflow as tf
import visualkeras

# Define your U-Net model here using build_unet
def build_unet():
    # ...
    return model

model = build_unet()  # build the model

# Define layer labels here
layer_labels = {
    'input_1': 'Input Image',
    'conv2d': 'Convolution',
    'max_pooling2d': 'Max Pooling',
    'conv2d_1': 'Convolution',
    'max_pooling2d_1': 'Max Pooling',
    'conv2d_2': 'Convolution',
    'up_sampling2d': 'Up Sampling',
    'concatenate': 'Concatenation',
    'conv2d_3': 'Convolution',
    'up_sampling2d_1': 'Up Sampling',
    'concatenate_1': 'Concatenation',
    'conv2d_4': 'Convolution',
    'conv2d_5': 'Convolution',
    'conv2d_6': 'Convolution',
    'conv2d_7': 'Convolution',
    'conv2d_8': 'Output'
}

visualkeras.layered_view(model, to_file='unet_model.png', legend=True, layer_labels=layer_labels)

history = model.fit(X_train, y_train, 
                    batch_size = 16, 
                    verbose=1, 
                    epochs=25, 
                    validation_data=(X_test, y_test), 
                    shuffle=False)

#Save the model for future use
model.save('/content/drive/MyDrive/Colab Notebooks/saved_models/tutorial118_mitochondria_25epochs.hdf5')

#plot the training and validation accuracy and loss at each epoch
loss = history.history['loss']
val_loss = history.history['val_loss']
epochs = range(1, len(loss) + 1)
plt.plot(epochs, loss, 'y', label='Training loss')
plt.plot(epochs, val_loss, 'r', label='Validation loss')
plt.title('Training and validation loss')
plt.xlabel('Epochs')
plt.ylabel('Loss')
plt.legend()
plt.show()

acc = history.history['accuracy']
val_acc = history.history['val_accuracy']
plt.plot(epochs, acc, 'y', label='Training acc')
plt.plot(epochs, val_acc, 'r', label='Validation acc')
plt.title('Training and validation accuracy')
plt.xlabel('Epochs')
plt.ylabel('Accuracy')
plt.legend()
plt.show()

plt.figure(figsize = (20,5))
plt.subplot(1,2,1)
plt.title("Train and Validation Loss")
plt.xlabel("Epoch")
plt.ylabel("Loss")
plt.plot(history.history['loss'],label="Train Loss")
plt.plot(history.history['val_loss'], label="Validation Loss")
plt.xlim(0, 25)
plt.ylim(0.0,5)
plt.legend()

plt.subplot(1,2,2)
plt.title("Train and Validation Accuracy")
plt.xlabel("Epoch")
plt.ylabel("Accuracy")
plt.plot(history.history['accuracy'], label="Train Accuracy")
plt.plot(history.history['val_accuracy'], label="Validation Accuracy")
plt.xlim(0, 25)
plt.ylim(0.5,1)
plt.legend()
plt.tight_layout()

#Load previously saved model
from keras.models import load_model
model = load_model("/content/drive/MyDrive/Colab Notebooks/saved_models/tutorial118_mitochondria_25epochs.hdf5", compile=False)

#IOU
y_pred=model.predict(X_test)
y_pred_thresholded = y_pred > 0.5

from tensorflow.keras.metrics import MeanIoU

n_classes = 2
IOU_keras = MeanIoU(num_classes=n_classes)  
IOU_keras.update_state(y_pred_thresholded, y_test)
print("Mean IoU =", IOU_keras.result().numpy())

threshold = 0.5
test_img_number = random.randint(0, len(X_test)-1)
test_img = X_test[test_img_number]
ground_truth=y_test[test_img_number]
test_img_input=np.expand_dims(test_img, 0)
print(test_img_input.shape)
prediction = (model.predict(test_img_input)[0,:,:,0] > 0.5).astype(np.uint8)
print(prediction.shape)

plt.figure(figsize=(16, 8))
plt.subplot(231)
plt.title('Testing Image')
plt.imshow(test_img[:,:,0], cmap='gray')
plt.subplot(232)
plt.title('Testing Label')
plt.imshow(ground_truth[:,:,0], cmap='gray')
plt.subplot(233)
plt.title('Prediction on test image')
plt.imshow(prediction, cmap='gray')

plt.show()

! pip3 install -U segmentation-models

!pip install -U -q segmentation-models
!pip install -q tensorflow==2.2.1
!pip install -q keras==2.5
import os
os.environ["SM_FRAMEWORK"] = "tf.keras"

import os
os.environ["SM_FRAMEWORK"] = "tf.keras"

from tensorflow import keras
import segmentation_models as sm

sm.set_framework('tf.keras')

BACKBONE = 'mobilenetv2'
preprocess_input = sm.get_preprocessing(BACKBONE)

IMG_HEIGHT = image_dataset.shape[1]
IMG_WIDTH  = image_dataset.shape[2]
IMG_CHANNELS = image_dataset.shape[3]

input_shape = (IMG_HEIGHT, IMG_WIDTH, IMG_CHANNELS)

N_ROWS = IMG_WIDTH
N_COLS = IMG_HEIGHT
N_LABELS = 1

from tensorflow.keras.models import Sequential

model_tl_unet = Sequential()
model_tl_unet.add(tf.keras.layers.Conv2D(filters = 3, kernel_size =2, padding = 'same', activation = 'relu', input_shape = (N_ROWS,N_COLS,1)))

model_tl_unet.add(sm.Unet(BACKBONE, input_shape=(N_COLS, N_ROWS, 3), classes=N_LABELS, activation='sigmoid', encoder_weights='imagenet', encoder_freeze=True))

model_tl_unet.summary()

optimizer = tf.keras.optimizers.experimental.SGD(learning_rate=0.01)

model_tl_unet.compile(optimizer=optimizer,
                      loss="binary_crossentropy",
                      metrics=['accuracy'])

path_experiment =  "lung_segmentation/segmentacion_binaria/models/Train2"

model_checkpoint_callback = tf.keras.callbacks.ModelCheckpoint(
    filepath=path_experiment + 'model_unet_transf.h5',
    monitor='val_loss',
    mode='min',
    save_best_only=True,
    verbose=1)

early_stopping = tf.keras.callbacks.EarlyStopping(
    monitor='val_loss',
    patience=5,
    verbose=1,
    mode='min',
    restore_best_weights=False
)

# tf.keras.utils.plot_model(
#     model_tl_unet,
#     to_file="model2.png",
#     show_shapes=True,
#     show_layer_names=True,
#     rankdir="TB",
#     expand_nested=True,
#     dpi=96,
# )

history_unet_transf = model_tl_unet.fit(X_train, y_train, 
                    batch_size = 16, 
                    verbose=1, 
                    epochs=100, 
                    validation_data=(X_test, y_test), 
                    shuffle=False)






# history_unet_transf = model_tl_unet.fit(X_train,y_train,epochs=EPOCHS,
#                                     validation_data=(X_test, y_test),
#                                     callbacks=[model_checkpoint_callback, early_stopping],
#                                     verbose=1)

#plot the training and validation accuracy and loss at each epoch
history = history_unet_transf
loss = history.history['loss']
val_loss = history.history['val_loss']
epochs = range(1, len(loss) + 1)
plt.plot(epochs, loss, 'y', label='Training loss')
plt.plot(epochs, val_loss, 'r', label='Validation loss')
plt.title('Training and validation loss')
plt.xlabel('Epochs')
plt.ylabel('Loss')
plt.legend()
plt.show()

acc = history.history['accuracy']
val_acc = history.history['val_accuracy']
plt.plot(epochs, acc, 'y', label='Training acc')
plt.plot(epochs, val_acc, 'r', label='Validation acc')
plt.title('Training and validation accuracy')
plt.xlabel('Epochs')
plt.ylabel('Accuracy')
plt.legend()
plt.show()