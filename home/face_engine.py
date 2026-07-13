# from deepface import DeepFace

# print("Loading FaceNet model...")
# FACENET_MODEL = DeepFace.build_model("Facenet")
# print("FaceNet loaded.")

from insightface.app import FaceAnalysis

app = FaceAnalysis(
    name='buffalo_s',
    providers=['CPUExecutionProvider']
)

app.prepare(ctx_id=-1)