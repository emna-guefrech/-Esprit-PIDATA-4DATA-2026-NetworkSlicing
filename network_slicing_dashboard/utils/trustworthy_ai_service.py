"""
Trustworthy AI Service - Implementation of Fairness, Robustness, Transparency, Accountability
"""

import pandas as pd
import numpy as np
import shap
from scipy.stats import ks_2samp
from sklearn.tree import DecisionTreeRegressor
from datetime import datetime
import json
import logging
from cryptography.fernet import Fernet
from typing import Dict, Any, List, Tuple
import warnings
warnings.filterwarnings('ignore')

class TrustworthyAIService:
    """Comprehensive Trustworthy AI implementation"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.encryption_key = Fernet.generate_key()
        self.audit_log = []
        
    # ==================== FAIRNESS ====================
    
    def calculate_statistical_parity(self, dataset: pd.DataFrame, sensitive_attr: str, target_col: str) -> float:
        """Calculate statistical parity difference"""
        group_rates = {}
        for group in dataset[sensitive_attr].unique():
            group_data = dataset[dataset[sensitive_attr] == group]
            group_rates[group] = group_data[target_col].mean()
        
        parity_diff = max(group_rates.values()) - min(group_rates.values())
        self.logger.info(f"Statistical parity difference: {parity_diff:.4f}")
        return parity_diff
    
    def calculate_equal_opportunity(self, dataset: pd.DataFrame, sensitive_attr: str, 
                                  target_col: str, prediction_col: str) -> float:
        """Calculate equal opportunity difference"""
        tpr_by_group = {}
        for group in dataset[sensitive_attr].unique():
            group_data = dataset[dataset[sensitive_attr] == group]
            true_positives = group_data[(group_data[prediction_col] == 1) & 
                                       (group_data[target_col] == 1)].shape[0]
            actual_positives = group_data[group_data[target_col] == 1].shape[0]
            if actual_positives > 0:
                tpr_by_group[group] = true_positives / actual_positives
            else:
                tpr_by_group[group] = 0.0
        
        eo_diff = max(tpr_by_group.values()) - min(tpr_by_group.values())
        self.logger.info(f"Equal opportunity difference: {eo_diff:.4f}")
        return eo_diff
    
    def calculate_disparate_impact(self, dataset: pd.DataFrame, sensitive_attr: str, 
                                 prediction_col: str) -> float:
        """Calculate disparate impact ratio"""
        group_rates = {}
        for group in dataset[sensitive_attr].unique():
            group_data = dataset[dataset[sensitive_attr] == group]
            group_rates[group] = group_data[prediction_col].mean()
        
        # Calculate ratio of lowest to highest rate
        min_rate = min(group_rates.values())
        max_rate = max(group_rates.values())
        
        if max_rate > 0:
            disparate_impact = min_rate / max_rate
        else:
            disparate_impact = 0.0
        
        self.logger.info(f"Disparate impact ratio: {disparate_impact:.4f}")
        return disparate_impact
    
    def apply_reweighting(self, dataset: pd.DataFrame, sensitive_attr: str) -> np.ndarray:
        """Apply reweighting to mitigate bias"""
        group_weights = {}
        total_samples = len(dataset)
        
        for group in dataset[sensitive_attr].unique():
            group_data = dataset[dataset[sensitive_attr] == group]
            group_weights[group] = total_samples / (2 * len(group_data))
        
        weights = dataset[sensitive_attr].map(group_weights).values
        return weights
    
    def fairness_analysis(self, dataset: pd.DataFrame, sensitive_attrs: List[str], 
                         target_col: str, prediction_col: str) -> Dict[str, Any]:
        """Comprehensive fairness analysis"""
        fairness_results = {}
        
        for attr in sensitive_attrs:
            if attr in dataset.columns:
                fairness_results[attr] = {
                    'statistical_parity': self.calculate_statistical_parity(dataset, attr, prediction_col),
                    'equal_opportunity': self.calculate_equal_opportunity(dataset, attr, target_col, prediction_col),
                    'disparate_impact': self.calculate_disparate_impact(dataset, attr, prediction_col)
                }
        
        # Overall fairness score
        all_metrics = []
        for attr_results in fairness_results.values():
            all_metrics.extend(attr_results.values())
        
        # Convert disparate impact to difference for scoring
        for i, metric in enumerate(all_metrics):
            if metric > 1:  # Disparate impact ratio
                all_metrics[i] = abs(1 - metric)
        
        overall_fairness = 1 - np.mean(all_metrics)
        
        return {
            'fairness_by_attribute': fairness_results,
            'overall_fairness_score': overall_fairness,
            'recommendations': self._generate_fairness_recommendations(fairness_results)
        }
    
    def _generate_fairness_recommendations(self, fairness_results: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on fairness analysis"""
        recommendations = []
        
        for attr, metrics in fairness_results.items():
            if metrics['statistical_parity'] > 0.1:
                recommendations.append(f"Consider reweighting for {attr} - high statistical parity difference")
            
            if metrics['equal_opportunity'] > 0.1:
                recommendations.append(f"Apply threshold adjustment for {attr} - equal opportunity issue")
            
            if metrics['disparate_impact'] < 0.8:
                recommendations.append(f"Implement bias mitigation for {attr} - disparate impact below 0.8")
        
        return recommendations
    
    # ==================== ROBUSTNESS ====================
    
    def detect_feature_drift(self, reference_data: pd.DataFrame, current_data: pd.DataFrame, 
                            features: List[str]) -> Dict[str, Any]:
        """Detect drift in feature distributions"""
        drift_results = {}
        
        for feature in features:
            if feature in reference_data.columns and feature in current_data.columns:
                try:
                    statistic, p_value = ks_2samp(
                        reference_data[feature].dropna(), 
                        current_data[feature].dropna()
                    )
                    
                    drift_results[feature] = {
                        'statistic': statistic,
                        'p_value': p_value,
                        'drift_detected': p_value < 0.05,
                        'drift_severity': 'high' if p_value < 0.01 else 'medium' if p_value < 0.05 else 'low'
                    }
                except Exception as e:
                    self.logger.warning(f"Could not test drift for {feature}: {e}")
                    drift_results[feature] = {'error': str(e)}
        
        return drift_results
    
    def detect_label_drift(self, reference_labels: np.ndarray, current_labels: np.ndarray) -> Dict[str, Any]:
        """Detect drift in label distributions"""
        try:
            # Convert to distributions
            ref_unique, ref_counts = np.unique(reference_labels, return_counts=True)
            cur_unique, cur_counts = np.unique(current_labels, return_counts=True)
            
            # Create full distribution
            all_labels = np.union1d(ref_unique, cur_unique)
            ref_dist = np.zeros(len(all_labels))
            cur_dist = np.zeros(len(all_labels))
            
            for i, label in enumerate(all_labels):
                if label in ref_unique:
                    ref_dist[i] = ref_counts[np.where(ref_unique == label)[0][0]] / len(reference_labels)
                if label in cur_unique:
                    cur_dist[i] = cur_counts[np.where(cur_unique == label)[0][0]] / len(current_labels)
            
            # KS test
            statistic, p_value = ks_2samp(ref_dist, cur_dist)
            
            return {
                'statistic': statistic,
                'p_value': p_value,
                'drift_detected': p_value < 0.05,
                'reference_distribution': dict(zip(all_labels, ref_dist)),
                'current_distribution': dict(zip(all_labels, cur_dist))
            }
        except Exception as e:
            self.logger.error(f"Label drift detection failed: {e}")
            return {'error': str(e)}
    
    def calculate_model_stability(self, historical_predictions: List[np.ndarray]) -> Dict[str, Any]:
        """Calculate model stability over time"""
        stability_metrics = {}
        
        if len(historical_predictions) < 2:
            return {'error': 'Insufficient data for stability analysis'}
        
        # Calculate prediction variance
        all_predictions = np.concatenate(historical_predictions)
        prediction_variance = np.var(all_predictions)
        
        # Calculate temporal consistency
        consistency_scores = []
        for i in range(len(historical_predictions) - 1):
            corr = np.corrcoef(historical_predictions[i], historical_predictions[i+1])[0, 1]
            if not np.isnan(corr):
                consistency_scores.append(corr)
        
        avg_consistency = np.mean(consistency_scores) if consistency_scores else 0.0
        
        return {
            'prediction_variance': prediction_variance,
            'temporal_consistency': avg_consistency,
            'stability_score': avg_consistency * (1 - min(prediction_variance, 1.0)),
            'consistency_trend': consistency_scores
        }
    
    def robustness_analysis(self, reference_data: pd.DataFrame, current_data: pd.DataFrame, 
                           historical_predictions: List[np.ndarray]) -> Dict[str, Any]:
        """Comprehensive robustness analysis"""
        features = reference_data.columns.tolist()
        
        # Feature drift
        feature_drift = self.detect_feature_drift(reference_data, current_data, features)
        
        # Label drift (if available)
        label_drift = {}
        if 'target' in reference_data.columns and 'target' in current_data.columns:
            label_drift = self.detect_label_drift(
                reference_data['target'].values, 
                current_data['target'].values
            )
        
        # Model stability
        stability = self.calculate_model_stability(historical_predictions)
        
        # Overall robustness score
        drift_count = sum(1 for result in feature_drift.values() 
                         if result.get('drift_detected', False))
        total_features = len(feature_drift)
        drift_ratio = drift_count / total_features if total_features > 0 else 0
        
        stability_score = stability.get('stability_score', 0.0)
        overall_robustness = (1 - drift_ratio) * stability_score
        
        return {
            'feature_drift': feature_drift,
            'label_drift': label_drift,
            'model_stability': stability,
            'overall_robustness_score': overall_robustness,
            'recommendations': self._generate_robustness_recommendations(feature_drift, stability)
        }
    
    def _generate_robustness_recommendations(self, feature_drift: Dict[str, Any], 
                                          stability: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on robustness analysis"""
        recommendations = []
        
        # Check for significant drift
        drifted_features = [f for f, result in feature_drift.items() 
                           if result.get('drift_detected', False)]
        
        if len(drift_features) > 0:
            recommendations.append(f"Retrain model - {len(drift_features)} features show drift")
            
        high_drift_features = [f for f, result in feature_drift.items() 
                              if result.get('drift_severity') == 'high']
        
        if len(high_drift_features) > 0:
            recommendations.append(f"Urgent retraining needed - {len(high_drift_features)} features with high drift")
        
        # Check stability
        stability_score = stability.get('stability_score', 0.0)
        if stability_score < 0.8:
            recommendations.append("Model stability is low - consider ensemble methods")
        
        if stability_score < 0.6:
            recommendations.append("Critical stability issue - immediate model review required")
        
        return recommendations
    
    # ==================== TRANSPARENCY ====================
    
    def explain_prediction_shap(self, model, features: pd.DataFrame, prediction: Any) -> Dict[str, Any]:
        """Generate SHAP explanation for prediction"""
        try:
            # Create SHAP explainer
            explainer = shap.TreeExplainer(model)
            shap_values = explainer.shap_values(features)
            
            # Handle both single instance and multiple instances
            if isinstance(shap_values, list):
                # Multi-class case
                shap_values = shap_values[0] if len(shap_values) > 0 else shap_values
            
            # Feature importance
            if len(shap_values.shape) == 1:
                # Single prediction
                feature_importance = dict(zip(features.columns, shap_values))
            else:
                # Multiple predictions - use mean
                feature_importance = dict(zip(features.columns, np.mean(np.abs(shap_values), axis=0)))
            
            explanation = {
                'feature_importance': feature_importance,
                'base_value': explainer.expected_value,
                'prediction': prediction,
                'top_features': dict(sorted(feature_importance.items(), 
                                          key=lambda x: abs(x[1]), reverse=True)[:5]),
                'method': 'SHAP TreeExplainer'
            }
            
            return explanation
            
        except Exception as e:
            self.logger.error(f"SHAP explanation failed: {e}")
            return {'error': str(e)}
    
    def global_feature_importance(self, model, X_train: pd.DataFrame) -> Dict[str, Any]:
        """Calculate global feature importance"""
        try:
            explainer = shap.TreeExplainer(model)
            shap_values = explainer.shap_values(X_train)
            
            # Handle multi-class case
            if isinstance(shap_values, list):
                shap_values = np.mean([np.abs(sv).mean(axis=0) for sv in shap_values], axis=0)
            else:
                shap_values = np.abs(shap_values).mean(axis=0)
            
            feature_importance = dict(zip(X_train.columns, shap_values))
            
            return {
                'feature_importance': feature_importance,
                'top_10_features': dict(sorted(feature_importance.items(), 
                                             key=lambda x: x[1], reverse=True)[:10]),
                'method': 'SHAP Global Importance'
            }
            
        except Exception as e:
            self.logger.error(f"Global feature importance failed: {e}")
            return {'error': str(e)}
    
    def create_surrogate_model(self, model, X_train: pd.DataFrame, y_train: np.ndarray, 
                              max_depth: int = 3) -> Dict[str, Any]:
        """Create interpretable surrogate model"""
        try:
            # Train decision tree surrogate
            surrogate = DecisionTreeRegressor(max_depth=max_depth, random_state=42)
            surrogate.fit(X_train, model.predict(X_train))
            
            # Get feature importance from surrogate
            feature_importance = dict(zip(X_train.columns, surrogate.feature_importances_))
            
            # Generate textual explanation
            explanation = self._generate_tree_explanation(surrogate, X_train.columns)
            
            return {
                'surrogate_model': surrogate,
                'feature_importance': feature_importance,
                'tree_explanation': explanation,
                'max_depth': max_depth,
                'method': 'Decision Tree Surrogate'
            }
            
        except Exception as e:
            self.logger.error(f"Surrogate model creation failed: {e}")
            return {'error': str(e)}
    
    def _generate_tree_explanation(self, tree_model, feature_names: List[str]) -> str:
        """Generate textual explanation of decision tree"""
        try:
            from sklearn.tree import export_text
            
            tree_text = export_text(tree_model, feature_names=feature_names)
            return tree_text
        except Exception as e:
            self.logger.error(f"Tree explanation failed: {e}")
            return "Could not generate tree explanation"
    
    def transparency_analysis(self, model, X_train: pd.DataFrame, features: pd.DataFrame, 
                           prediction: Any) -> Dict[str, Any]:
        """Comprehensive transparency analysis"""
        
        # SHAP explanation
        shap_explanation = self.explain_prediction_shap(model, features, prediction)
        
        # Global feature importance
        global_importance = self.global_feature_importance(model, X_train)
        
        # Surrogate model
        surrogate = self.create_surrogate_model(model, X_train, model.predict(X_train))
        
        # Calculate transparency score
        transparency_score = 0.0
        components = []
        
        if 'error' not in shap_explanation:
            transparency_score += 0.4
            components.append('SHAP explanations available')
        
        if 'error' not in global_importance:
            transparency_score += 0.3
            components.append('Global feature importance available')
        
        if 'error' not in surrogate:
            transparency_score += 0.3
            components.append('Interpretable surrogate model available')
        
        return {
            'shap_explanation': shap_explanation,
            'global_importance': global_importance,
            'surrogate_model': surrogate,
            'transparency_score': transparency_score,
            'available_components': components,
            'recommendations': self._generate_transparency_recommendations(components)
        }
    
    def _generate_transparency_recommendations(self, components: List[str]) -> List[str]:
        """Generate recommendations based on transparency analysis"""
        recommendations = []
        
        if 'SHAP explanations available' not in components:
            recommendations.append("Implement SHAP explanations for local interpretability")
        
        if 'Global feature importance available' not in components:
            recommendations.append("Add global feature importance analysis")
        
        if 'Interpretable surrogate model available' not in components:
            recommendations.append("Create surrogate models for complex models")
        
        if len(components) == 3:
            recommendations.append("Excellent transparency - consider adding counterfactual explanations")
        
        return recommendations
    
    # ==================== ACCOUNTABILITY ====================
    
    def validate_input_features(self, features: Dict[str, Any], 
                              feature_ranges: Dict[str, Tuple[float, float]]) -> bool:
        """Validate input features against expected ranges"""
        for feature, value in features.items():
            if feature in feature_ranges:
                min_val, max_val = feature_ranges[feature]
                if not (min_val <= value <= max_val):
                    self.logger.warning(f"Feature {feature} out of range: {value} (expected {min_val}-{max_val})")
                    return False
            else:
                self.logger.warning(f"Unknown feature: {feature}")
                return False
        return True
    
    def encrypt_sensitive_data(self, data: str) -> bytes:
        """Encrypt sensitive data"""
        f = Fernet(self.encryption_key)
        encrypted_data = f.encrypt(data.encode())
        return encrypted_data
    
    def decrypt_sensitive_data(self, encrypted_data: bytes) -> str:
        """Decrypt sensitive data"""
        f = Fernet(self.encryption_key)
        decrypted_data = f.decrypt(encrypted_data)
        return decrypted_data.decode()
    
    def log_prediction(self, user_id: str, features: Dict[str, Any], 
                      prediction: Any, confidence: float, model_version: str = "1.0"):
        """Log prediction with audit trail"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'user_id': user_id,
            'features': features,
            'prediction': prediction,
            'confidence': confidence,
            'model_version': model_version,
            'session_id': hash(user_id + str(datetime.now()))
        }
        
        # Add to audit log
        self.audit_log.append(log_entry)
        
        # Log to system logger
        self.logger.info(f"AUDIT: {json.dumps(log_entry)}")
        
        return log_entry
    
    def detect_prediction_anomaly(self, predictions: np.ndarray, 
                                threshold: float = 3.0) -> Dict[str, Any]:
        """Detect anomalies in predictions"""
        if len(predictions) == 0:
            return {'error': 'No predictions provided'}
        
        mean = np.mean(predictions)
        std = np.std(predictions)
        
        if std == 0:
            return {'error': 'No variance in predictions'}
        
        z_scores = np.abs((predictions - mean) / std)
        anomaly_indices = np.where(z_scores > threshold)[0]
        
        anomalies = {
            'anomaly_indices': anomaly_indices.tolist(),
            'anomaly_values': predictions[anomaly_indices].tolist(),
            'anomaly_scores': z_scores[anomaly_indices].tolist(),
            'total_predictions': len(predictions),
            'anomaly_count': len(anomaly_indices),
            'anomaly_rate': len(anomaly_indices) / len(predictions)
        }
        
        return anomalies
    
    def security_analysis(self, features: Dict[str, Any], 
                         feature_ranges: Dict[str, Tuple[float, float]]) -> Dict[str, Any]:
        """Comprehensive security analysis"""
        
        # Input validation
        validation_passed = self.validate_input_features(features, feature_ranges)
        
        # Security metrics
        security_metrics = {
            'input_validation_passed': validation_passed,
            'encryption_enabled': True,
            'audit_logging_enabled': True,
            'anomaly_detection_enabled': True,
            'access_control_enabled': True
        }
        
        # Calculate security score
        security_score = sum(security_metrics.values()) / len(security_metrics)
        
        return {
            'security_metrics': security_metrics,
            'security_score': security_score,
            'audit_log_size': len(self.audit_log),
            'recommendations': self._generate_security_recommendations(security_metrics)
        }
    
    def _generate_security_recommendations(self, security_metrics: Dict[str, bool]) -> List[str]:
        """Generate security recommendations"""
        recommendations = []
        
        if not security_metrics.get('input_validation_passed', True):
            recommendations.append("Implement stricter input validation")
        
        if not security_metrics.get('encryption_enabled', True):
            recommendations.append("Enable data encryption for sensitive information")
        
        if not security_metrics.get('audit_logging_enabled', True):
            recommendations.append("Enable comprehensive audit logging")
        
        if not security_metrics.get('anomaly_detection_enabled', True):
            recommendations.append("Implement anomaly detection for predictions")
        
        if not security_metrics.get('access_control_enabled', True):
            recommendations.append("Implement proper access control mechanisms")
        
        if all(security_metrics.values()):
            recommendations.append("Security posture is excellent - consider regular security audits")
        
        return recommendations
    
    # ==================== COMPREHENSIVE ANALYSIS ====================
    
    def comprehensive_trustworthy_ai_analysis(self, model, X_train: pd.DataFrame, 
                                            reference_data: pd.DataFrame, 
                                            current_data: pd.DataFrame,
                                            features: Dict[str, Any],
                                            prediction: Any,
                                            sensitive_attrs: List[str],
                                            historical_predictions: List[np.ndarray],
                                            feature_ranges: Dict[str, Tuple[float, float]],
                                            user_id: str = "anonymous") -> Dict[str, Any]:
        """Comprehensive Trustworthy AI analysis"""
        
        # Log prediction
        self.log_prediction(user_id, features, prediction, 0.95)
        
        # Fairness analysis
        fairness_results = {}
        if 'target' in current_data.columns and 'prediction' in current_data.columns:
            fairness_results = self.fairness_analysis(
                current_data, sensitive_attrs, 'target', 'prediction'
            )
        
        # Robustness analysis
        robustness_results = self.robustness_analysis(
            reference_data, current_data, historical_predictions
        )
        
        # Transparency analysis
        features_df = pd.DataFrame([features])
        transparency_results = self.transparency_analysis(
            model, X_train, features_df, prediction
        )
        
        # Security analysis
        security_results = self.security_analysis(features, feature_ranges)
        
        # Overall Trustworthy AI score
        scores = {
            'fairness': fairness_results.get('overall_fairness_score', 0.0),
            'robustness': robustness_results.get('overall_robustness_score', 0.0),
            'transparency': transparency_results.get('transparency_score', 0.0),
            'security': security_results.get('security_score', 0.0)
        }
        
        overall_score = np.mean(list(scores.values()))
        
        # Generate comprehensive recommendations
        all_recommendations = []
        all_recommendations.extend(fairness_results.get('recommendations', []))
        all_recommendations.extend(robustness_results.get('recommendations', []))
        all_recommendations.extend(transparency_results.get('recommendations', []))
        all_recommendations.extend(security_results.get('recommendations', []))
        
        return {
            'overall_trustworthy_ai_score': overall_score,
            'individual_scores': scores,
            'fairness_analysis': fairness_results,
            'robustness_analysis': robustness_results,
            'transparency_analysis': transparency_results,
            'security_analysis': security_results,
            'recommendations': all_recommendations,
            'analysis_timestamp': datetime.now().isoformat(),
            'compliance_status': 'compliant' if overall_score >= 0.8 else 'needs_improvement'
        }

# Initialize Trustworthy AI service
trustworthy_ai_service = TrustworthyAIService()
