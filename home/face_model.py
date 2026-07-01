from deepface import DeepFace

print("Loading FaceNet model...")
FACENET_MODEL = DeepFace.build_model("Facenet")
print("FaceNet loaded.")