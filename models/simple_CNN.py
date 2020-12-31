import argparse
import tensorflow as tf
import tensorflow_addons as tfa

from tensorflow.keras import datasets, layers, models, losses, optimizers
import matplotlib.pyplot as plt
from functools import partial

import dataset

# Global variables field
ConvNN2D = partial(layers.Conv2D,
                        kernel_size=3, activation='relu', padding="SAME")

MaxPool2DPartial = partial(layers.MaxPooling2D, pool_size=2)
AvrPool2DPartial = partial(layers.AveragePooling2D, pool_size=(2, 2), strides=None, padding="valid", data_format=None)

device_name = tf.test.gpu_device_name()
if device_name != '/device:GPU:0':
    raise SystemError('GPU device not found')
print('Found GPU at: {}'.format(device_name))

def plot_accuracy_loss_epoch(history, model, num_epochs, loss_option=True):
    train_loss_score = history.history['loss']
    validation_loss_score = history.history['val_loss']
    
    train_acc_score = history.history['accuracy']
    validation_acc_score = history.history['val_accuracy']

    x_axis_epochs = range(num_epochs)
    plt.figure(figsize=(9,9))
    plt.subplot(1,2,1)
    plt.plot(x_axis_epochs, train_acc_score, label='Training Accuracy')
    plt.plot(x_axis_epochs, validation_acc_score, label='Validation Accuracy')
    plt.legend(loc='upper left')
    plt.title('Training and Validation Accuracy vs Number of Epochs')

    plt.subplot(1,2,2)
    plt.plot(x_axis_epochs, train_loss_score, label='Training Loss')
    plt.plot(x_axis_epochs, validation_loss_score, label='Validation Loss')
    plt.legend(loc='lower left')
    plt.title('Training and Validation Loss vs Number of Epochs')
    plt.show()

class NaiveCNN:
    def initialise_datasets(self, ds_class_name):
        self.X_train, self.y_train, self.X_valid, self.y_valid, self.X_test, self.y_test = ds_class_name.import_data_augment()
        self.dataset = ds_class_name.dataset_name
        self.num_channels = ds_class_name.get_num_channels()
        self.img_height = ds_class_name.height
        self.img_width = ds_class_name.width

    def construct_cnn_v1(act_args_units=['relu', 'relu', 'softmax', 128, 64, 10]):
        n = len(act_args_units)//2
        activation_args = act_args_units[:n]
        units = act_args_units[n:]
        assert(n == len(units))
        model = models.Sequential([
            ConvNN2D(filters=64, kernel_size=7, input_shape=[32, 32, num_channels]), #format of cifar images = (32, 32, 3)
            layers.MaxPooling2D(pool_size=2),
            ConvNN2D(filters=128),
            ConvNN2D(filters=128),
            layers.MaxPooling2D(pool_size=2),
            ConvNN2D(filters=256),
            ConvNN2D(filters=256),
            layers.MaxPooling2D(pool_size=2),
            layers.Flatten()])  #Flatten (unroll) the 2D output to 1D
            for i in range(n):
                model.add(layers.Dense(units= units[i], activation=activation_args[i]))
                if i != (n-1):
                    model.add(layers.Dropout(0.5))
        ])
        model.summary() #-> to check output dimensionality
        return model

    def construct_cnn_v2():
        model = models.Sequential([
            ConvNN2D(filters=64, kernel_size=3, input_shape=[img_height, img_width, num_channels]),
            ConvNN2D(filters=64, kernel_size=3),
            ConvNN2D(filters=128, kernel_size=3, strides=2),
            ConvNN2D(filters=128, kernel_size=3),
            layers.Dropout(0.5),
            ConvNN2D(filters=128, kernel_size=3),
            ConvNN2D(filters=192, kernel_size=3, strides=2),
            ConvNN2D(filters=192, kernel_size=3),
            layers.Dropout(0.5),
            ConvNN2D(filters=192, kernel_size=3),
            AvrPool2DPartial(kernel_size=8),
            ConvNN2D(filters=class_num, kernel_size=1, padding="valid")
        ])
        model.summary()
        return model

    def compile_fit_model(self, loss_fun, select_optimizer, metrics_options, num_epochs, plot_verbose, loss_option):
        #self.model.compile(loss=loss_fun, optimizer=select_optimizer, metrics=metrics_options)   #try with "adam" optimiser as well, metrics = ["sparse_categorical_accuracy"]
        self.model.compile(optimizer=select_optimizer, loss=loss_fun, metrics=metrics_options)
        self.history = self.model.fit(self.X_train, self.y_train, epochs = num_epochs, validation_data=(self.X_valid, self.y_valid))
        self.test_score = self.model.evaluate(self.X_test, self.y_test, verbose=2)  #test_loss,test_acc -> will need these for the sequential class addition performance evaluation
        #y_pred = self.model.predict(self.X_test)
        if plot_verbose:
            plot_accuracy_loss_epoch(self.history, self.model, num_epochs, loss_option)


    def compile_fit_GPU(self, opt_GPU=False, loss_fun=args.loss_fun, select_optimizer=args.optimizer, metrics_options=[args.metrics], num_epochs=args.num_epochs, plot_verbose=True):
        if select_optimizer == "SGDW":  # lr = 0.1 , momentum = , weight_decay = , epoch_num = 200
            lr = args.lr
            len_ds = len(X_train)+len(X_valid)+len(X_test)+len(y_train)+len(y_valid)+len(y_test)
            num_steps = 80*(len_ds/args.batch_size)
            select_optimizer = tfa.optimizers.SGDW(learning_rate=optimizers.schedules.PiecewiseConstantDecay(boundaries=[num_steps, num_steps], values=[lr, (lr + 0.1), (lr + 0.2)]), momentum=args.momentum, weight_decay=args.weight_decay) #TODO: for SGDW, loss_fun should be sparse categorical cross-entropy(?)
        if opt_GPU:
            with tf.device('/device:GPU:0'):
                compile_fit_model(loss_fun, select_optimizer, metrics_options, plot_verbose)
        else:
            compile_fit_model(loss_fun, select_optimizer, metrics_options, plot_verbose)

    def __init__(self, ds_name, construct_cnn = construct_cnn_v2):
        self.model = construct_cnn_v2()
        initialise_datasets(ds_name)


def args_parse():
    parser = argparse.ArgumentParser(description='Supply naive CNN with hyper-parameter configuration & options')
    # will add for architecture/model used for the multiple models used
    #The parameters for our model compilation
    compile_env = parser.add_argument_group(title="Model Compilation")
    compile_env.add_argument('--optimizer', '-o', default='adam', type=str, help='')
    compile_env.add_argument('--loss-fn', '-lf', default='sparse_categorical_crossentropy', type=str, help='')
    compile_env.add_argument('--metrics', '-me', default='sparse_categorical_accuracy', type=str, help='')
    compile_env.add_argument('--momentum', '-mo', default=1, type=float, help='')
    compile_env.add_argument('--weight_decay', '-wd', default=1, type=float, help='')

    #The parameters for our training dataset
    train_env = parser.add_argument_group(title="Parameters for Training Dataset")
    train_env.add_argument('--batch-size', '-b', default=32, type=int, help='')
    train_env.add_argument('--num-epochs', '-e', default=10, type=int, help='')

    args = parser.parse_args()
    return args
    

if __name__ == "__main__":
    args = args_parse()

    naiveCNN = NaiveCNN(ds_name=Cifar10.CIFAR10)
    naiveCNN.model.compile_fit_GPU(opt_GPU=True)
    test_loss, test_acc = naiveCNN.test_score
    print(f"The Loss for our model & test dataset is {test_loss} and the Accuracy for our model & test dataset is {test_acc} ")

    