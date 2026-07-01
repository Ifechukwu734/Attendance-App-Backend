from deepface import DeepFace

print("Loading FaceNet512 model...")
FACENET_MODEL = DeepFace.build_model("Facenet512")
print("FaceNet512 loaded.")