from src.wine_quality_prediction.config.configuration import ConfigurationManager
from src.wine_quality_prediction.components.model_evaluation import ModelEvaluation
from src.wine_quality_prediction import logger

STAGE_NAME = "Model evaluation stage"


class ModelEvaluationTrainingPipeline:
    def __init__(self):
        pass

    def initiate_model_evaluation(self):
        try:
            config = ConfigurationManager()
            model_evaluation_config = config.get_model_evaluation_config()
            model_evaluation = ModelEvaluation(config=model_evaluation_config)

            logger.info("Starting model evaluation...")
            model_evaluation.log_into_mlflow()
            logger.info("Model evaluation completed successfully!")

        except Exception as e:
            logger.error(f"Model evaluation pipeline failed: {str(e)}")
            raise e
