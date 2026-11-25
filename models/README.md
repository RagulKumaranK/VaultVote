# VaultVote Biometric Models

This directory contains the pretrained deep learning model weights used by the VaultVote biometric verification pipeline.

---

## 1. YuNet Face Detector (`face_detection_yunet_2023mar.onnx`)

* **Architecture:** YuNet (CNN-based lightweight and high-speed face detector)
* **Author / Source:** Shiqi Yu, OpenCV Zoo ([opencv/opencv_zoo](https://github.com/opencv/opencv_zoo))
* **License:** Apache License 2.0
* **Input Tensor:** Dynamic `[1, 3, H, W]` (BGR image format, $0 - 255$)
* **Output Tensor:** `[N, 15]`
  * Indices `0..3`: Bounding box `[x, y, w, h]`
  * Indices `4..13`: 5 facial landmarks (right eye, left eye, nose tip, right mouth corner, left mouth corner)
  * Index `14`: Face detection confidence score ($0.0 - 1.0$)
* **Purpose:** Real-time face detection, background noise filtering (e.g., curtain folds), and 5-point facial landmark alignment.

---

## 2. ArcFace MobileFaceNet (`w600k_mbf.onnx`)

* **Architecture:** MobileFaceNet with ArcFace (Additive Angular Margin) Loss
* **Source:** InsightFace Project / deepghs ([InsightFace Buffalo_S Model Zoo](https://github.com/deepinsight/insightface))
* **Training Dataset:** MS1MV3 / Glint360k
* **License:** MIT License / Academic Research License
* **Input Tensor:** `[1, 3, 112, 112]` (RGB image format, normalized $(x - 127.5) / 128.0$)
* **Output Tensor:** `[1, 512]` ($L_2$-normalized facial identity embedding)
* **Matching Metric:** Cosine similarity ($\mathbf{e}_1 \cdot \mathbf{e}_2$)
* **Calibrated Threshold:** $\tau = 0.50$ (scores $\ge 0.50$ indicate genuine match; scores $< 0.50$ indicate impostor mismatch)
* **Purpose:** Generates 512-dimensional facial identity embeddings for 1:1 biometric identity verification against registered voter records.

---

## 3. SFace Face Recognizer (`face_recognition_sface_2021dec.onnx`)

* **Architecture:** SphereFace / SFace ResNet-based face recognition model
* **Source:** OpenCV Zoo
* **License:** Apache License 2.0
* **Input Tensor:** `[1, 3, 112, 112]`
* **Output Tensor:** `[1, 128]`
* **Purpose:** Secondary/backup facial recognition descriptor.
