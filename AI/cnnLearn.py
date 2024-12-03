import os
import numpy as np
import cv2
from sklearn.model_selection import train_test_split
import tensorflow as tf
from tensorflow.keras import layers, models

# 함수 정의
def read_and_resize_images(directory, label):
    images = []
    labels = []
    for filename in os.listdir(directory):
        if filename.endswith(".png"): #학습시킬 파일의 확장자명
            image = cv2.imread(os.path.join(directory, filename))
            image = cv2.resize(image, (80, 80)) #이미지 크기, app과 통일
            images.append(image)
            labels.append(label)
    return images, labels

# 이미지 로드 및 resizing
cat1_images, cat1_labels = read_and_resize_images("./cat1", label=0)
cat2_images, cat2_labels = read_and_resize_images("./cat2", label=1)
cat3_images, cat3_labels = read_and_resize_images("./cat3", label=2)
cat4_images, cat4_labels = read_and_resize_images("./cat4", label=3)
cat5_images, cat5_labels = read_and_resize_images("./cat5", label=4)
cat6_images, cat6_labels = read_and_resize_images("./cat6", label=5)
cat7_images, cat7_labels = read_and_resize_images("./cat7", label=6)
cat8_images, cat8_labels = read_and_resize_images("./cat8", label=7)
cat9_images, cat9_labels = read_and_resize_images("./cat9", label=8)
cat10_images, cat10_labels = read_and_resize_images("./cat10", label=9)
cat11_images, cat11_labels = read_and_resize_images("./cat11", label=10)


# 데이터 합치고 훈련 및 테스트 세트로 나누기
X = np.array(cat1_images + cat2_images + cat3_images + cat4_images + cat5_images + cat6_images + cat7_images + cat8_images + cat9_images + cat10_images + cat11_images)
y = np.array(cat1_labels + cat2_labels + cat3_labels + cat4_labels + cat5_labels + cat6_labels + cat7_labels + cat8_labels + cat9_labels + cat10_labels + cat11_labels)

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# CNN 모델 만들기 및 훈련
model = models.Sequential([
    layers.Conv2D(32, (3, 3), activation='relu', input_shape=(80, 80, 3)),
    layers.MaxPooling2D((2, 2)),
    layers.Conv2D(64, (3, 3), activation='relu'),
    layers.MaxPooling2D((2, 2)),
    layers.Conv2D(128, (3, 3), activation='relu'),
    layers.MaxPooling2D((2, 2)),
    layers.Conv2D(128, (3, 3), activation='relu'),
    layers.MaxPooling2D((2, 2)),
    layers.Flatten(),
    layers.Dense(512, activation='relu'),
    layers.Dropout(0.35),
    layers.Dense(11, activation='softmax')  # x개의 클래스
])

model.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['accuracy'])

history = model.fit(X_train, y_train, epochs=50, batch_size=16, validation_split=0.2)

# 모델 평가
test_loss, test_acc = model.evaluate(X_test, y_test)
print("Test accuracy:", test_acc)

import matplotlib.pyplot as plt
from sklearn.metrics import roc_curve, auc
from sklearn.preprocessing import label_binarize

# 테스트 데이터에 대한 예측 확률 계산
y_score = model.predict(X_test)

# 각 클래스에 대한 이진 분류를 위해 레이블 이진화
y_test_bin = label_binarize(y_test, classes=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10])  # x개의 클래스(6개일시 0~5)

# 클래스마다 ROC 곡선 및 AUC 계산
fpr = dict()
tpr = dict()
roc_auc = dict()
for i in range(11):  # x개의 클래스
    fpr[i], tpr[i], _ = roc_curve(y_test_bin[:, i], y_score[:, i])
    roc_auc[i] = auc(fpr[i], tpr[i])

# 모든 클래스에 대한 ROC 그래프 그리기
plt.figure(figsize=(8, 6))
for i in range(11):  # x개의 클래스
    plt.plot(fpr[i], tpr[i], label=f'Class {i} (AUC = {roc_auc[i]:.2f})')

plt.plot([0, 1], [0, 1], 'k--')
plt.xlim([0.0, 1.0])
plt.ylim([0.0, 1.05])
plt.xlabel('False Positive Rate')
plt.ylabel('True Positive Rate')
plt.title('ROC Curve for Multi-class Classification')
plt.legend(loc="lower right")
plt.show()

# 모델 저장
model.save("cat_cnn_model.h5") #model의 파일명
print("Model saved as cat_cnn_model.h5")