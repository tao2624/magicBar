import sys
import os
import numpy as np
import tensorflow as tf
from tensorflow.keras import layers, models, optimizers, losses, callbacks, utils  # type: ignore TensorFlow
from tensorflow.keras.preprocessing.sequence import pad_sequences  # type: ignore TensorFlow
from sklearn.metrics import classification_report       # pip install scikit-learn
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QPushButton, QLabel, QVBoxLayout, QWidget, \
    QMessageBox
import re

# 动作分类名
motion_names = [
    'RightAngle', 'SharpAngle', 'Lightning', 'Triangle', 'Letter_h', 'letter_R',
    'letter_W', 'letter_phi', 'Circle', 'UpAndDown', 'Horn', 'Wave', 'NoMotion'
]

# 定义目录路径和文件名
DEF_MODEL_NAME = 'model.h5'
DEF_WEIGHTS_NAME = 'weights.h'
DEF_FILE_MAX = 100
DEF_N_ROWS = 150 # 每个文件最多读取的行数
DEF_COLUMNS = (3, 4, 5)
DEF_FILE_FORMAT = '.txt'
DEF_FILE_NAME_SEPERATOR = '_'
DEF_BATCH_SIZE = 120
DEF_NUM_EPOCH = 200

# 动作名称到标签的映射
motion_to_label = {name: idx for idx, name in enumerate(motion_names)}


# 定义训练函数
def train(x_train, y_train, x_test, y_test, model_path, weights_path,
          input_shape=(DEF_N_ROWS, 3, 1), num_classes=len(motion_names),
          batch_size=DEF_BATCH_SIZE, epochs=DEF_NUM_EPOCH):
    inputs = layers.Input(shape=input_shape)
    x = layers.Conv2D(30, kernel_size=(3, 3), strides=(3, 1), padding='same')(inputs)
    x = layers.LeakyReLU()(x)
    x = layers.Conv2D(15, kernel_size=(3, 3), strides=(3, 1), padding='same')(x)
    x = layers.LeakyReLU()(x)
    x = layers.AveragePooling2D(pool_size=(3, 1), strides=(3, 1))(x)
    x = layers.Flatten()(x)
    x = layers.Dense(num_classes)(x)
    outputs = layers.Softmax()(x)

    model = models.Model(inputs=inputs, outputs=outputs)
    model.compile(optimizer=optimizers.Adam(), loss=losses.CategoricalCrossentropy(), metrics=['accuracy'])

    early_stopping = callbacks.EarlyStopping(monitor='val_loss', patience=10)
    checkpoint = callbacks.ModelCheckpoint(model_path, monitor='val_accuracy', save_best_only=True, mode='max')

    history = model.fit(x_train, y_train, batch_size=batch_size, epochs=epochs, verbose=2,
                        validation_data=(x_test, y_test), shuffle=True,
                        callbacks=[early_stopping, checkpoint])

    # Save the model weights
    model.save_weights(weights_path)

    del model
    tf.keras.backend.clear_session()

    return history


# 加载数据集函数
def load_dataset(root_dir, max_rows=None):
    file_list = []
    labels = []
    for filename in os.listdir(root_dir):
        if filename.endswith(DEF_FILE_FORMAT):
            match = re.match(rf'^([\w]+)_([\d]+){DEF_FILE_FORMAT}$', filename)
            if match:
                motion_name = match.group(1)    # 取正则表达式中第一个捕获组内容 为motion_name
                number_str = match.group(2)     # 取正则表达式中第二个捕获组内容 为number_str
                number = int(number_str)    # 将编号字符串转换为整数
                if 0 <= number <= DEF_FILE_MAX:
                    if motion_name in motion_to_label:
                        file_path = os.path.join(root_dir, filename)    # 拼接文件完整路径
                        # delimiter=' '：指定文件中数据的分隔符为空格
                        # usecols=DEF_COLUMNS：指定要加载的列索引
                        data = np.loadtxt(file_path, delimiter=' ', usecols=DEF_COLUMNS, max_rows=max_rows)
                        print(f"load data: {data}")
                        file_list.append(data)
                        labels.append(motion_to_label[motion_name])
                    else:
                        print(f"Motion name not recognized: {filename}")
                else:
                    print(f"Number out of range: {filename}")
            else:
                print(f"Invalid file name format: {filename}")
    return file_list, labels


# PyQt5 界面定义
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("训练模型")
        self.setGeometry(100, 100, 400, 300)

        self.label = QLabel("请选择数据文件夹", self)
        self.select_button = QPushButton("选择数据文件夹", self)
        self.train_button = QPushButton("开始训练", self)
        self.model_path_button = QPushButton("选择模型保存路径", self)
        self.weights_path_button = QPushButton("选择权重保存路径", self)
        self.model_path_label = QLabel("模型保存路径: 未选择", self)
        self.weights_path_label = QLabel("权重保存路径: 未选择", self)

        self.select_button.clicked.connect(self.select_directory)
        self.train_button.clicked.connect(self.start_training)
        self.model_path_button.clicked.connect(self.select_model_path)
        self.weights_path_button.clicked.connect(self.select_weights_path)

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.select_button)
        layout.addWidget(self.model_path_label)
        layout.addWidget(self.weights_path_label)
        layout.addWidget(self.model_path_button)
        layout.addWidget(self.weights_path_button)
        layout.addWidget(self.train_button)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.data_directory = ""
        self.model_path = DEF_MODEL_NAME
        self.weights_path = DEF_WEIGHTS_NAME

    def select_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "选择数据文件夹")
        if directory:
            self.data_directory = directory
            self.label.setText(f"选择的文件夹: {self.data_directory}")

    def select_model_path(self):
        path, _ = QFileDialog.getSaveFileName(self, "选择模型保存路径", DEF_MODEL_NAME,
                                              "HDF5 Files (*.h5);;All Files (*)")
        if path:
            self.model_path = path
            self.model_path_label.setText(f"模型保存路径: {self.model_path}")

    def select_weights_path(self):
        # getSaveFileName返回两个元素：一个是完整路径，另一个是用户选择的文件过滤器信息。_即忽视掉第二个参数
        path, _ = QFileDialog.getSaveFileName(self, "选择权重保存路径", DEF_WEIGHTS_NAME,
                                              "HDF5 Files (*.h5);;All Files (*)")
        if path:
            self.weights_path = path
            self.weights_path_label.setText(f"权重保存路径: {self.weights_path}")

    def start_training(self):
        if not self.data_directory:
            QMessageBox.warning(self, "警告", "请先选择数据文件夹")
            return
        if self.model_path == DEF_MODEL_NAME:
            QMessageBox.warning(self, "警告", "请先选择模型保存路径")
            return
        if self.weights_path == DEF_WEIGHTS_NAME:
            QMessageBox.warning(self, "警告", "请先选择权重保存路径")
            return

        # 加载数据集
        file_list, labels = load_dataset(self.data_directory, max_rows=DEF_N_ROWS)

        # 数据预处理
        max_len = max([len(x) for x in file_list])
        file_list_padded = pad_sequences(file_list, maxlen=max_len, dtype='float32', padding='post', value=0)
        labels_one_hot = utils.to_categorical(labels, num_classes=len(motion_names))

        # 数据集分割
        num_elements = len(file_list_padded)
        train_size = int(num_elements * 0.8)

        best_val_accuracy = 0
        best_model = None
        for _ in range(3):
            indices = np.arange(num_elements)
            np.random.shuffle(indices)

            train_indices = indices[:train_size]
            test_indices = indices[train_size:]

            x_train = file_list_padded[train_indices]
            y_train = labels_one_hot[train_indices]
            x_test = file_list_padded[test_indices]
            y_test = labels_one_hot[test_indices]

            history = train(x_train, y_train, x_test, y_test, model_path=self.model_path,
                            weights_path=self.weights_path, batch_size=DEF_BATCH_SIZE, epochs=DEF_NUM_EPOCH)

            model = tf.keras.models.load_model(self.model_path)

            y_pred = model.predict(x_test)
            y_pred_classes = np.argmax(y_pred, axis=1)
            y_true_classes = np.argmax(y_test, axis=1)

            val_accuracy = history.history['val_accuracy'][-1]
            print(f"Validation Accuracy: {val_accuracy:.4f}")

            if val_accuracy > best_val_accuracy:
                best_val_accuracy = val_accuracy
                best_model = model

        if best_model is not None:
            y_pred = best_model.predict(x_test)
            y_pred_classes = np.argmax(y_pred, axis=1)
            y_true_classes = np.argmax(y_test, axis=1)

            print(classification_report(y_true_classes, y_pred_classes, target_names=motion_names))

            QMessageBox.information(self, "训练完成", "模型训练完成，最佳模型及其权重已保存。")
        else:
            QMessageBox.warning(self, "训练失败", "没有找到最佳模型。")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())