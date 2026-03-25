import os
import pickle as pkl
from functools import lru_cache
from django.conf import settings


@lru_cache(maxsize=1)
def load_bundle():
    """
    Loads the trained ML model bundle.
    Bundle must contain:
        {
            "model": trained_model,
            "feature_cols": [list_of_feature_names]
        }
    """

    # Absolute path to pickle file
    pkl_path = os.path.join(
        settings.BASE_DIR,
        "recommender",
        "ml",
        "Crop_recommendation_RF.pkl"
    )

    # Check file exists
    if not os.path.exists(pkl_path):
        raise FileNotFoundError(
            f"Model file not found at: {pkl_path}"
        )

    # Load pickle
    with open(pkl_path, "rb") as f:
        bundle = pkl.load(f)

    # Validate structure
    if not isinstance(bundle, dict):
        raise ValueError("Invalid model bundle: Must be a dictionary.")

    if "model" not in bundle or "feature_cols" not in bundle:
        raise ValueError(
            "Invalid model bundle structure. Required keys: 'model', 'feature_cols'"
        )

    return bundle

def predict_one(feature_dict):
    """
    feature_dict example:
    {
        "N": 90,
        "P": 40,
        "K": 40,
        "temperature": 20,
        "humidity": 80,
        "ph": 7,
        "rainfall": 200
    }
    """

    bundle = load_bundle()

    model = bundle["model"]
    feature_order = bundle["feature_cols"]

    # Ensure all required features are present
    missing = [col for col in feature_order if col not in feature_dict]
    if missing:
        raise ValueError(f"Missing features: {missing}")

    # Convert to ordered list
    X = [[float(feature_dict[col]) for col in feature_order]]
    pred = model.predict(X)[0]
    return pred