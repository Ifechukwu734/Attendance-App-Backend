# import cv2
# import numpy as np
# from .face_engine import app


# def get_embedding(image_path):
#     image = cv2.imread(image_path)

#     if image is None:
#         return None
    
#     faces = app.get(image)

#     if len(faces) == 0:
#         return None
#     return faces[0].embedding



# def cosine_similarity(vec1, vec2):
#     return np.dot(vec1, vec2) / (
#         np.linalg.norm(vec1) * np.linalg.norm(vec2)
#     )

# def verify_faces(image1_path, image2_path, threshold=0.6):
#     emb1 = get_embedding(image1_path)
#     emb2 = get_embedding(image2_path)

#     if emb1 is None:
#         return {
#             'success': False,
#             'message': 'No face detected in first image'
#         }
    
#     if emb2 is None:
#         return {
#             'success': False,
#             'message': 'No face detected in second image'
#         }
    
#     similarity = cosine_similarity(emb1, emb2)

#     return {
#         'success': True,
#         'matched': similarity >= threshold,
#         'similarity': round(float(similarity), 4)
#     }