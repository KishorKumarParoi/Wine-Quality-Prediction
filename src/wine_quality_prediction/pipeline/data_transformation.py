from src.wine_quality_prediction.config.configuration import ConfigurationManager
from src.wine_quality_prediction.components.data_transformation import (
    DataTransformation,
)
from src.wine_quality_prediction import logger

from pathlib import Path


STAGE_NAME = "Data Transformation Stage"


class DataTransformationTrainingPipeline:
    def __init__(self):
        pass

    def initiate_data_transformation(self):
        try:
            with open(
                Path("artifacts/data_validation/status.txt"), "r", encoding="utf-8"
            ) as f:
                status = f.read().split(" ")[-1].strip()

            logger.info(f"Validation status: {status}")

            if status == "True":
                config = ConfigurationManager()
                data_transformation_config = config.get_data_transformation_config()
                data_transformation = DataTransformation(
                    config=data_transformation_config
                )
                data_transformation.train_test_spliting()
                logger.info(f"{STAGE_NAME} completed successfully")
            else:
                raise ValueError(f"Data validation failed with status: {status}")

        except Exception as e:
            logger.error(f"{STAGE_NAME} failed with error: {str(e)}")
            raise e
