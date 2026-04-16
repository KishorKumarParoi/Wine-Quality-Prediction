import os
import pandas as pd
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from urllib.parse import urlparse
import mlflow
from mlflow import sklearn
import numpy as np
import joblib
from src.wine_quality_prediction import logger
import pathlib
from src.wine_quality_prediction.utils.common import save_json
from src.wine_quality_prediction.entity.config_entity import ModelEvaluationConfig
from pathlib import Path


# import os
# os.environ["MLFLOW_TRACKING_URI"]="https://dagshub.com/KishorKumarParoi/Wine-Quality-Prediction.mlflow"
# os.environ["MLFLOW_TRACKING_USERNAME"]="KishorKumarParoi"
# os.environ["MLFLOW_TRACKING_PASSWORD"]="c0edb772affc440233d8431ecf491d2e577ec401"


class ModelEvaluation:
    def __init__(self, config: ModelEvaluationConfig):
        self.config = config

    def eval_metrics(self, actual, pred):
        """Calculate evaluation metrics"""
        rmse = np.sqrt(mean_squared_error(actual, pred))
        mae = mean_absolute_error(actual, pred)
        r2 = r2_score(actual, pred)
        return rmse, mae, r2

    def log_into_mlflow(self):
        """Log model metrics and model to MLflow"""
        try:
            test_data = pd.read_csv(self.config.test_data_path)
            model = joblib.load(self.config.model_path)

            test_x = test_data.drop([self.config.target_column], axis=1)
            test_y = test_data[[self.config.target_column]]

            mlflow.set_registry_uri(self.config.mlflow_uri)
            tracking_url_type_store = urlparse(mlflow.get_tracking_uri()).scheme

            with mlflow.start_run():
                predicted_qualities = model.predict(test_x)
                (rmse, mae, r2) = self.eval_metrics(test_y, predicted_qualities)

                # Save metrics locally
                scores = {"rmse": rmse, "mae": mae, "r2": r2}
                save_json(path=Path(self.config.metric_file_name), data=scores)
                logger.info("Metrics saved: %s", scores)

                # Log parameters
                mlflow.log_params(self.config.all_params)
                logger.info("Parameters logged to MLflow")

                # Log metrics
                mlflow.log_metric("rmse", rmse)
                mlflow.log_metric("mae", mae)
                mlflow.log_metric("r2", r2)
                logger.info(
                    "Metrics logged to MLflow - RMSE: %.4f, MAE: %.4f, R2: %.4f",
                    rmse,
                    mae,
                    r2,
                )

                # Try to register model, but don't fail if it doesn't work
                if tracking_url_type_store != "file":
                    try:
                        sklearn.log_model(
                            model,
                            name="model",
                            serialization_format="skops",
                            registered_model_name="ElasticnetModel",
                        )
                        logger.info("Model registered successfully")
                    except Exception as e:
                        logger.warning("Model registration failed: %s", str(e))
                        logger.info("Logging model without registration")
                        sklearn.log_model(
                            model, name="model", serialization_format="skops"
                        )
                else:
                    sklearn.log_model(model, name="model", serialization_format="skops")
                    logger.info("Model logged to local MLflow")

        except Exception as e:
            logger.error("MLflow logging failed: %s", str(e))
            raise e
