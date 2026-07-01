from deepface import DeepFace

print("Downloading FaceNet512...")
DeepFace.build_model("Facenet")
print("Done.")