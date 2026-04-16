from src.wine_quality_prediction.config.configuration import ConfigurationManager
from src.wine_quality_prediction.components.data_validation import DataValidation
from src.wine_quality_prediction import logger

STAGE_NAME = "Data Validation Stage"


class DataValidationTrainingPipeline:
    def __init__(self):
        pass

    def initiate_data_validation(self):
        config = ConfigurationManager()
        data_validation_config = config.get_data_validation_config()
        data_validation = DataValidation(config=data_validation_config)

        # Run all validation checks
        print("=" * 50)
        print("Running Data Validation Checks...")
        print("=" * 50)

        # Check columns
        col_status = data_validation.validate_all_columns()
        print(f"Column Validation: {'PASSED' if col_status else 'FAILED'}")

        # Check data types
        type_status = data_validation.validate_data_types()
        print(f"Type Validation: {'PASSED' if type_status else 'FAILED'}")

        # Check missing values
        missing_status = data_validation.validate_missing_values()
        print(f"Missing Values Validation: {'PASSED' if missing_status else 'FAILED'}")

        print("=" * 50)
        overall_status = col_status and type_status
        print(
            f"Overall Validation Status: {'PASSED ✓' if overall_status else 'FAILED ✗'}"
        )
        print("=" * 50)


if __name__ == "__main__":
    try:
        logger.info(f">>>>>> stage {STAGE_NAME} started <<<<<<")
        obj = DataValidationTrainingPipeline()
        obj.initiate_data_validation()
        logger.info(f">>>>>> stage {STAGE_NAME} completed <<<<<<\n\nx==========x")
    except Exception as e:
        logger.exception(e)
        raise e
