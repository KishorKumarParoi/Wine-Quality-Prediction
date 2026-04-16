"""
Wine Quality Prediction API
===========================
A Flask-based REST API for predicting wine quality using machine learning.

This module provides endpoints to:
- Display the prediction form (GET /)
- Make predictions (POST /predict)
- Train the pipeline (GET /train)
- Health check (GET /health)

Author: Kishor Kumar Paroi
Version: 1.0.0
"""

import os
import logging
import sys
import subprocess
from typing import Tuple, Union
from pathlib import Path
import numpy as np
import pandas as pd
from flask import Flask, render_template, request, jsonify

from src.wine_quality_prediction import logger
from src.wine_quality_prediction.pipeline.final_prediction import PredictionPipeline


# ========================
# Flask App Configuration
# ========================
app = Flask(__name__)
app.config["JSON_SORT_KEYS"] = False
app.config["JSONIFY_PRETTYPRINT_REGULAR"] = True

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


# ========================
# Constants
# ========================
FEATURE_NAMES = [
    "fixed acidity",
    "volatile acidity",
    "citric acid",
    "residual sugar",
    "chlorides",
    "free sulfur dioxide",
    "total sulfur dioxide",
    "density",
    "pH",
    "sulphates",
    "alcohol",
]

EXPECTED_FEATURES = 11


# ========================
# Helper Functions
# ========================
def validate_input(data: list) -> Tuple[bool, str]:
    """
    Validate input data for prediction.

    Args:
        data: List of floats representing wine features

    Returns:
        Tuple of (is_valid, error_message)
    """
    if len(data) != EXPECTED_FEATURES:
        return False, f"Expected {EXPECTED_FEATURES} features, got {len(data)}"

    for i, value in enumerate(data):
        try:
            float(value)
        except (ValueError, TypeError):
            return False, f"Feature '{FEATURE_NAMES[i]}' must be a valid number"

    return True, ""


def format_prediction(prediction: float) -> dict:
    """
    Format the prediction output with quality assessment.

    Args:
        prediction: Raw prediction value (0-10)

    Returns:
        Dictionary with formatted prediction and assessment
    """
    prediction = float(prediction)

    if prediction >= 7:
        quality = "Excellent"
        emoji = "🌟"
    elif prediction >= 5:
        quality = "Good"
        emoji = "✨"
    elif prediction >= 3:
        quality = "Average"
        emoji = "⭐"
    else:
        quality = "Below Average"
        emoji = "💧"

    return {"score": round(prediction, 2), "quality": quality, "emoji": emoji}


# ========================
# Routes - Home & Health
# ========================
@app.route("/", methods=["GET"])
def home_page():
    """
    Home page - Display the prediction form.

    Returns:
        Rendered HTML template for the prediction form
    """
    logger.info("User accessed home page")
    return render_template("index.html")


@app.route("/health", methods=["GET"])
def health_check():
    """
    Health check endpoint for monitoring.

    Returns:
        JSON response indicating API health status
    """
    logger.info("Health check requested")
    return (
        jsonify(
            {
                "status": "healthy",
                "service": "Wine Quality Predictor",
                "version": "1.0.0",
            }
        ),
        200,
    )


# ========================
# Routes - Prediction
# ========================
@app.route("/predict", methods=["POST", "GET"])
def predict():
    """
    Prediction endpoint - Accept wine features and return quality prediction.

    POST Parameters:
        - fixed_acidity (float)
        - volatile_acidity (float)
        - citric_acid (float)
        - residual_sugar (float)
        - chlorides (float)
        - free_sulfur_dioxide (float)
        - total_sulfur_dioxide (float)
        - density (float)
        - pH (float)
        - sulphates (float)
        - alcohol (float)

    Returns:
        HTML template with prediction result or form
    """
    if request.method == "POST":
        try:
            logger.info("Prediction request received")

            # Extract features from form
            features = [
                float(request.form.get("fixed_acidity", 0)),
                float(request.form.get("volatile_acidity", 0)),
                float(request.form.get("citric_acid", 0)),
                float(request.form.get("residual_sugar", 0)),
                float(request.form.get("chlorides", 0)),
                float(request.form.get("free_sulfur_dioxide", 0)),
                float(request.form.get("total_sulfur_dioxide", 0)),
                float(request.form.get("density", 0)),
                float(request.form.get("pH", 0)),
                float(request.form.get("sulphates", 0)),
                float(request.form.get("alcohol", 0)),
            ]

            # Validate input
            is_valid, error_msg = validate_input(features)
            if not is_valid:
                logger.error(f"Invalid input: {error_msg}")
                return render_template("error.html", error=error_msg), 400

            # Make prediction
            logger.info(f"Processing prediction with features: {features}")
            data_array = np.array(features).reshape(1, EXPECTED_FEATURES)

            pipeline = PredictionPipeline()
            prediction = pipeline.predict(data_array)

            # Format prediction result
            result = format_prediction(prediction[0])
            logger.info(f"Prediction successful: {result}")

            return render_template(
                "results.html",
                prediction=result["score"],
                quality=result["quality"],
                emoji=result["emoji"],
            )

        except ValueError as e:
            logger.error(f"Value error in prediction: {str(e)}")
            return (
                render_template(
                    "error.html",
                    error="Invalid input values. Please enter valid numbers.",
                ),
                400,
            )

        except FileNotFoundError as e:
            logger.error(f"Model file not found: {str(e)}")
            return (
                render_template(
                    "error.html", error="Model not found. Please train the model first."
                ),
                500,
            )

        except Exception as e:
            logger.error(f"Unexpected error in prediction: {str(e)}")
            return (
                render_template(
                    "error.html",
                    error="An error occurred while making the prediction. Please try again.",
                ),
                500,
            )

    else:
        # GET request - return form
        return render_template("index.html")


# ========================
# Routes - Training
# ========================
@app.route("/train", methods=["GET"])
def train_model():
    """
    Training endpoint - Execute the complete ML pipeline.

    This endpoint runs the training pipeline including:
    - Data ingestion
    - Data validation
    - Data transformation
    - Model training
    - Model evaluation

    Returns:
        JSON response with training status
    """
    try:
        logger.info("Training pipeline initiated via web interface")

        # Get project root and resolve paths
        project_root = Path(__file__).parent.absolute()
        main_script = project_root / "main.py"

        # Prepare environment with MLflow credentials
        env = os.environ.copy()
        env["MLFLOW_TRACKING_URI"] = (
            "https://dagshub.com/KishorKumarParoi/Wine-Quality-Prediction.mlflow"
        )
        env["MLFLOW_TRACKING_USERNAME"] = "KishorKumarParoi"
        env["MLFLOW_TRACKING_PASSWORD"] = "c0edb772affc440233d8431ecf491d2e577ec401"
        env["PYTHONPATH"] = str(project_root)

        # Run using subprocess.run() for better control
        result = subprocess.run(
            [sys.executable, str(main_script)],
            cwd=str(project_root),
            env=env,
            capture_output=True,
            text=True,
            timeout=3600,  # 1 hour timeout
        )

        if result.returncode == 0:
            logger.info("Training pipeline completed successfully")
            return (
                jsonify(
                    {
                        "status": "success",
                        "message": "Training pipeline completed successfully!",
                        "timestamp": pd.Timestamp.now().isoformat(),
                        "details": "All 5 pipeline stages completed (Ingestion, Validation, Transformation, Training, Evaluation)",
                    }
                ),
                200,
            )
        else:
            error_output = result.stderr[:500] if result.stderr else "Unknown error"
            logger.error(f"Training pipeline failed: {result.stderr}")
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "Training pipeline failed. Check logs for details.",
                        "error_details": error_output,
                    }
                ),
                500,
            )

    except subprocess.TimeoutExpired:
        logger.error("Training pipeline timed out after 1 hour")
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "Training pipeline timed out (exceeded 1 hour)",
                }
            ),
            504,
        )
    except Exception as e:
        logger.error(f"Error during training: {str(e)}")
        return (
            jsonify({"status": "error", "message": f"Training failed: {str(e)}"}),
            500,
        )


# ========================
# Error Handlers
# ========================
@app.errorhandler(404)
def page_not_found(error):
    """Handle 404 errors."""
    logger.warning(f"404 error: {error}")
    return render_template("error.html", error="Page not found"), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    logger.error(f"500 error: {error}")
    return render_template("error.html", error="Internal server error"), 500


# ========================
# Main Entry Point
# ========================
if __name__ == "__main__":

    # Start the Flask development server.

    # Configuration:
    # - Host: 0.0.0.0 (accessible from all network interfaces)
    # - Port: 8080
    # - Debug: False (set to True for development)

    logger.info("Starting Wine Quality Predictor API")
    logger.info("Server running on http://0.0.0.0:8080")

    app.run(host="0.0.0.0", port=8080, debug=False, use_reloader=True)
