from keras.layers import *
from keras.callbacks import TensorBoard, ModelCheckpoint, EarlyStopping
from keras.optimizers import *
from keras.models import Model
from keras.initializers import *
from keras import regularizers

import time

class KerasModel:
    def __init__(self, prefix='model_multitask', epochs=100, focus=1,
            focus_value=1, lr=0.1, layers=1, size=500, momentum=0.7, nesterov=True, batch_size=500,
            decay=1e-4, l2=0.002, loss_weights = None, dropout=0):
        self.prefix = prefix
        self.epochs = epochs
        self.focus = focus
        self.focus_value = focus_value
        self.lr = lr
        self.layers = layers
        self.size = size
        self.momentum = momentum
        self.nesterov = nesterov
        self.batch_size = batch_size
        self.decay = decay
        self.l2 = l2
        self.loss_weights = loss_weights
        self.dropout = dropout


    def create_model(self, in_count, out_count):
        if (self.loss_weights != None):
            loss_weights = dict([('pred_' + str(i), v) for i, v in enumerate(self.loss_weights)])
        else:
            loss_weights = dict(map(lambda i: ('pred_' + str(i), 1), range(out_count)))
        # if (self.focus != -1):
        #     loss_weights['pred_' + str(self.focus)] = self.focus_value

        print(loss_weights)

        input_layer = Input(shape=(in_count,))
        x = input_layer
        # x = BatchNormalization()(x)
        for i in range(self.layers):
            x = Dense(self.size, kernel_initializer='normal', activation='relu', kernel_regularizer=regularizers.l2(self.l2))(x)
            # x = BatchNormalization()(x)
            x = Dropout(self.dropout)(x)


        # middles = [BatchNormalization()(Dense(100, kernel_initializer='normal', activation='relu',
        #     kernel_regularizer=regularizers.l2(self.l2), name='middle_' + str(i))(x)) for i in range(out_count)]

        outputs = [Dense(1, kernel_initializer='normal', activation='sigmoid',
            kernel_regularizer=regularizers.l2(self.l2), name='pred_' + str(i))(x) for i in range(out_count)]


        model = Model(inputs=[input_layer], outputs=outputs)
        # opt=Adam(lr=self.lr, decay=self.decay)
        opt=SGD(lr=self.lr, momentum=self.momentum, nesterov=self.nesterov, decay=self.decay)
        
        model.compile(opt, 
                        loss='binary_crossentropy',
                        metrics=['mae'],
                        loss_weights=loss_weights)

        return model;


    def get_callbacks(self):
        timestamp = int(time.time())
        if (self.focus == -1):
            monitor_name = 'val_loss'
        else:
            monitor_name = 'val_pred_' + str(self.focus) + '_loss'

        self.weights_filename = self.prefix + str(timestamp)
        tensor_board_cb = TensorBoard(log_dir='./logs/tfboard' + str(timestamp))
        model_checkpoint = ModelCheckpoint('./'+self.weights_filename, monitor=monitor_name, 
                                         save_best_only=True, verbose=1, save_weights_only=True)
        # early_stopping = EarlyStopping(monitor=monitor_name, patience=20, verbose=0)
        return [tensor_board_cb]


    def fit(self, X_train, train_targets):
        model = self.create_model(X_train.shape[1], len(train_targets))
        model.fit(X_train, train_targets, epochs=self.epochs,
                  batch_size=self.batch_size, callbacks=self.get_callbacks(),
                  validation_split=0, verbose=1) # validation is done with 1% of training!
        # model.load_weights('./'+self.weights_filename)
        return model;