import os
import pandas as pd
from sklearn.linear_model import ElasticNet
import joblib
from src.wine_quality_prediction import logger
from src.wine_quality_prediction.config.configuration import ConfigurationManager
from src.wine_quality_prediction.components.model_trainer import ModelTrainer


STAGE_NAME = "Model Trainer Stage"


class ModelTrainerTrainingPipeline:
    def __init__(self):
        pass

    def initiate_model_trainer(self):
        try:
            with open(
                os.path.join("artifacts/data_validation/status.txt"),
                "r",
                encoding="utf-8",
            ) as f:
                status = f.read().split(" ")[-1].strip()

            logger.info(f"Validation status: {status}")

            if status == "True":
                config = ConfigurationManager()
                model_trainer_config = config.get_model_trainer_config()
                model_trainer = ModelTrainer(config=model_trainer_config)
                model_trainer.train()
                logger.info(f"Model training completed successfully")
            else:
                raise ValueError(f"Data validation failed with status: {status}")

        except Exception as e:
            logger.error(f"Model training failed with error: {str(e)}")
            raise e


if __name__ == "__main__":
    try:
        model_trainer_pipeline = ModelTrainerTrainingPipeline()
        model_trainer_pipeline.initiate_model_trainer()
    except Exception as e:
        logger.exception(e)
        raise e
