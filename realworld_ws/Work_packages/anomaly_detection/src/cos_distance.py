import helper
from scipy.spatial.distance import cosine

def run(known_good_paths, known_bad_paths, unknown_paths):
    model = helper.load_model(device='cpu')

    known_good_embeddings = [helper.get_embedding(model, p) for p in known_good_paths]
    known_bad_embeddings = [helper.get_embedding(model, p) for p in known_bad_paths]
    unknown_embeddings = [helper.get_embedding(model, p) for p in unknown_paths]

    distances = helper.cosine_distances(known_good_embeddings, known_bad_embeddings, unknown_embeddings)

    probabilities = []

    for path, distance in zip(unknown_paths, distances):
        avg_distance_to_good = distance["avg_distance_to_good"]

        if avg_distance_to_good is not None:
            probability = avg_distance_to_good
        else:
            probability = None

        probabilities.append({
            "unknown_path": path,
            "probability": probability
        })

    return probabilities