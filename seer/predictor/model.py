"""
ML model for threat prediction.
"""

import numpy as np
from typing import Dict, List, Any, Tuple, Optional
import logging
import pandas as pd
import joblib
import os
from datetime import datetime, timedelta

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ThreatPredictor:
    """Threat predictor for forecasting cyber threats."""
    
    def __init__(self, model_path: Optional[str] = None):
        """Initialize the threat predictor.
        
        Args:
            model_path: Path to the saved model file
        """
        self.model = None
        
        if model_path and os.path.exists(model_path):
            try:
                self.model = joblib.load(model_path)
                logger.info(f"Loaded model from {model_path}")
            except Exception as e:
                logger.error(f"Failed to load model: {str(e)}")
        else:
            logger.warning("No model loaded. Predictions will use default heuristics.")
    
    def predict_threat_probability(self, 
                                  threat_data: Dict[str, Any]) -> float:
        """Predict the probability of a threat materializing.
        
        Args:
            threat_data: Threat data for prediction
            
        Returns:
            Probability of the threat materializing (0-1)
        """
        # This is a placeholder. In a real application, you would use a trained model.
        
        # If we have a model, use it
        if self.model:
            try:
                # Extract features from threat_data
                features = self._extract_features(threat_data)
                
                # Make prediction
                probability = self.model.predict_proba([features])[0][1]
                return probability
            except Exception as e:
                logger.error(f"Model prediction failed: {str(e)}")
                # Fall back to heuristic
        
        # Simple heuristic based on confidence and severity
        confidence = threat_data.get("confidence", 50) / 100.0
        
        severity_map = {
            "LOW": 0.3,
            "MEDIUM": 0.5,
            "HIGH": 0.7,
            "CRITICAL": 0.9,
            "UNKNOWN": 0.5
        }
        
        severity_factor = severity_map.get(threat_data.get("severity", "UNKNOWN").upper(), 0.5)
        
        # Calculate a simple probability
        probability = (confidence * 0.7) + (severity_factor * 0.3)
        
        return probability
    
    def forecast_threats(self, 
                        historical_data: List[Dict[str, Any]], 
                        days_ahead: int = 7) -> List[Dict[str, Any]]:
        """Forecast threats based on historical data.
        
        Args:
            historical_data: List of historical threat data
            days_ahead: Number of days to forecast
            
        Returns:
            List of forecasted threats
        """
        # This is a simple placeholder implementation
        
        # Group threats by category
        categories = {}
        for threat in historical_data:
            category = threat.get("category", "Unknown")
            if category not in categories:
                categories[category] = []
            categories[category].append(threat)
        
        forecasts = []
        today = datetime.utcnow()
        
        for category, threats in categories.items():
            # Calculate frequency (threats per day)
            days_span = (threats[-1].get("timestamp", today) - threats[0].get("timestamp", today - timedelta(days=30))).days
            days_span = max(days_span, 1)  # Avoid division by zero
            frequency = len(threats) / days_span
            
            # Calculate average severity
            severity_map = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4, "UNKNOWN": 2}
            avg_severity = sum(severity_map.get(t.get("severity", "UNKNOWN").upper(), 2) for t in threats) / len(threats)
            
            # Generate forecast for each day
            for day in range(1, days_ahead + 1):
                forecast_date = today + timedelta(days=day)
                
                # Simple prediction: if frequency > 0.3 per day, predict a threat
                if frequency > 0.3:
                    # Determine severity based on average
                    severity = "LOW"
                    if avg_severity > 3:
                        severity = "CRITICAL"
                    elif avg_severity > 2.5:
                        severity = "HIGH"
                    elif avg_severity > 1.5:
                        severity = "MEDIUM"
                    
                    forecasts.append({
                        "category": category,
                        "predicted_date": forecast_date,
                        "severity": severity,
                        "probability": min(frequency * 0.8, 0.95),  # Cap at 95%
                        "confidence": min(frequency * 60, 90)  # Cap at 90
                    })
        
        # Sort by probability (highest first)
        forecasts.sort(key=lambda x: x.get("probability", 0), reverse=True)
        
        return forecasts
    
    def _extract_features(self, threat_data: Dict[str, Any]) -> List[float]:
        """Extract features from threat data for model prediction.
        
        Args:
            threat_data: Threat data
            
        Returns:
            List of feature values
        """
        # This is a placeholder. In a real application, you would extract relevant features.
        features = []
        
        # Add confidence
        features.append(threat_data.get("confidence", 50) / 100.0)
        
        # Add severity as a numeric value
        severity_map = {"LOW": 0.25, "MEDIUM": 0.5, "HIGH": 0.75, "CRITICAL": 1.0, "UNKNOWN": 0.5}
        features.append(severity_map.get(threat_data.get("severity", "UNKNOWN").upper(), 0.5))
        
        # Add number of potential targets
        features.append(min(len(threat_data.get("potential_targets", [])) / 10.0, 1.0))
        
        # Add dummy features to complete the feature vector expected by the model
        # In a real application, these would be actual features
        features.extend([0.5, 0.5, 0.5, 0.5])
        
        return features
    
    def train_model(self, 
                   training_data: List[Dict[str, Any]], 
                   labels: List[int], 
                   model_path: str) -> bool:
        """Train a new prediction model.
        
        Args:
            training_data: List of threat data for training
            labels: List of outcome labels (1 = materialized, 0 = did not materialize)
            model_path: Path to save the trained model
            
        Returns:
            True if training was successful
        """
        try:
            from sklearn.ensemble import RandomForestClassifier
            
            # Extract features from training data
            X = [self._extract_features(data) for data in training_data]
            y = labels
            
            # Create and train the model
            model = RandomForestClassifier(n_estimators=100, random_state=42)
            model.fit(X, y)
            
            # Save the model
            joblib.dump(model, model_path)
            
            # Update the current model
            self.model = model
            
            logger.info(f"Model trained and saved to {model_path}")
            return True
        except Exception as e:
            logger.error(f"Model training failed: {str(e)}")
            return False


# Create a default predictor instance
predictor = ThreatPredictor() 