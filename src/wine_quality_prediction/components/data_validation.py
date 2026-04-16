import os
from src.wine_quality_prediction import logger
import pandas as pd

from src.wine_quality_prediction.entity.config_entity import DataValidationConfig


class DataValidation:
    def __init__(self, config: DataValidationConfig):
        self.config = config

    def validate_all_columns(self) -> bool:
        """Validate that all required columns exist in the dataset"""
        try:
            validation_status = True
            data = pd.read_csv(self.config.unzip_data_dir)
            all_cols = list(data.columns)
            all_schema = set(self.config.all_schema.keys())

            # Check if all schema columns exist in data
            missing_cols = all_schema - set(all_cols)
            if missing_cols:
                validation_status = False
                logger.error(f"Missing columns in data: {missing_cols}")
                self._write_status(validation_status)
                return validation_status

            # Check if data has any extra columns not in schema
            extra_cols = set(all_cols) - all_schema
            if extra_cols:
                validation_status = False
                logger.error(f"Extra columns in data not in schema: {extra_cols}")
                self._write_status(validation_status)
                return validation_status

            logger.info("All columns validation passed")
            self._write_status(validation_status)
            return validation_status

        except Exception as e:
            logger.error(f"Column validation failed: {str(e)}")
            self._write_status(False)
            raise e

    def validate_data_types(self) -> bool:
        """Validate that data types match the schema"""
        try:
            validation_status = True
            data = pd.read_csv(self.config.unzip_data_dir)

            type_mapping = {
                "int": ["int64", "int32", "int"],
                "float": ["float64", "float32", "float"],
                "object": ["object", "string"],
                "string": ["object", "string"],
            }

            for column, dtype in self.config.all_schema.items():
                col_dtype = str(data[column].dtype)
                expected_type = dtype.get("dtype") if isinstance(dtype, dict) else dtype

                allowed_types = type_mapping.get(
                    str(expected_type), [str(expected_type)]
                )

                if col_dtype not in allowed_types:
                    validation_status = False
                    logger.error(
                        f"Type mismatch for column '{column}': expected {expected_type}, got {col_dtype}"
                    )
                else:
                    logger.info(
                        f"Column '{column}' type validation passed: {col_dtype}"
                    )

            self._write_status(validation_status)
            return validation_status

        except Exception as e:
            logger.error(f"Type validation failed: {str(e)}")
            self._write_status(False)
            raise e

    def validate_missing_values(self) -> bool:
        """Validate missing values in the dataset"""
        try:
            validation_status = True
            data = pd.read_csv(self.config.unzip_data_dir)

            missing_counts = data.isnull().sum()
            if missing_counts.sum() > 0:
                logger.warning(
                    f"Missing values found:\n{missing_counts[missing_counts > 0]}"
                )
                validation_status = False
            else:
                logger.info("No missing values found")

            self._write_status(validation_status)
            return validation_status

        except Exception as e:
            logger.error(f"Missing values validation failed: {str(e)}")
            self._write_status(False)
            raise e

    def _write_status(self, status: bool):
        """Helper method to write validation status to file"""
        try:
            with open(self.config.STATUS_FILE, "w") as f:
                f.write(f"Validation status: {status}\n")
            logger.info(f"Validation status written to {self.config.STATUS_FILE}")
        except Exception as e:
            logger.error(f"Failed to write status file: {str(e)}")
            raise e
