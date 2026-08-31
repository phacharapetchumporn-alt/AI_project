import tensorflow as tf

# 1. โหลดโมเดล Keras ที่เทรนไว้
model = tf.keras.models.load_model("action_model.h5")  # หรือ filename.keras

# 2. แปลงเป็น TFLite
converter = tf.lite.TFLiteConverter.from_keras_model(model)

# Optimizations (ช่วยให้ไฟล์เล็กลงและรันบนมือถือเร็วขึ้น)
converter.optimizations = [tf.lite.Optimize.DEFAULT]

tflite_model = converter.convert()

# 3. บันทึกเป็นไฟล์ .tflite
with open("action_model.tflite", "wb") as f:
    f.write(tflite_model)

print("Export TFLite สำเร็จ! ได้ไฟล์ action_model.tflite เรียบร้อย")