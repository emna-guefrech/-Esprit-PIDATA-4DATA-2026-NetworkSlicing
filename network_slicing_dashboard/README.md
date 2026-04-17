# Network Slicing Intelligence — 5G & 6G

A comprehensive MLOps web dashboard for network slicing management across both 5G and 6G networks, featuring real-time ML predictions for congestion classification and QoS probability estimation.

## 🌐 Project Overview

This platform provides intelligent network slicing predictions to help network operators:
- Predict network congestion levels (Normal/Light/Critical)
- Estimate QoS SLA compliance probabilities
- Make data-driven resource allocation decisions
- Maintain service level agreements proactively

## 🚀 Quick Start

### Installation
```bash
# Clone the repository
git clone <repository-url>
cd network_slicing_dashboard

# Install dependencies
pip install -r requirements.txt

# Run the dashboard
streamlit run app.py
```

The dashboard will open in your browser at `http://localhost:8501`

## 📁 Project Structure

```
network_slicing_dashboard/
├── app.py                           ← Main Streamlit entry point
├── models/                          ← Model storage directory
│   ├── model_6G_5_1_xgboost.joblib  ← 6G congestion classification model
│   ├── model_6G_5_2_xgboost.joblib  ← 6G QoS probability regression model
│   ├── model_6G_5_3.joblib          ← 6G Objective 5.3 (placeholder)
│   ├── model_5G_A.joblib            ← 5G Objective A (placeholder)
│   ├── model_5G_B.joblib            ← 5G Objective B (placeholder)
│   └── model_5G_C.joblib            ← 5G Objective C (placeholder)
├── pages/                           ← Multi-page navigation
│   ├── 01_6G_objective_5_1.py       ← 6G congestion classification
│   ├── 02_6G_objective_5_2.py       ← 6G QoS probability regression
│   ├── 03_6G_objective_5_3.py       ← 6G placeholder for Eya
│   ├── 04_5G_objective_A.py         ← 5G placeholder for friend
│   ├── 05_5G_objective_B.py         ← 5G placeholder for friend
│   └── 06_5G_objective_C.py         ← 5G placeholder for friend
├── utils/                           ← Utility functions
│   ├── model_loader.py              ← Model loading with fallback
│   └── predict.py                   ← Prediction logic per objective
├── requirements.txt                 ← Python dependencies
└── README.md                        ← This file
```

## 🎯 Available Objectives

### 6G Network Slicing — Eya's Dataset (🔵 Purple)

**Objective 5.1 - Network Congestion Classification**
- **Model:** XGBoost Classifier
- **Performance:** F1-Score: 0.9775
- **Features:** 12 network metrics (latency, packet loss, jitter, etc.)
- **Output:** Congestion class (Normal/Light/Critical) with business recommendations

**Objective 5.2 - QoS Probability Regression**
- **Model:** XGBoost Regressor (Tuned)
- **Performance:** R²=0.8537, RMSE=0.0162
- **Features:** 4 gap metrics (Latency_Gap, Packet_Loss_Gap, Jitter_Gap, Rate_Gap)
- **Output:** SLA compliance probability (0-1) with risk assessment

**Objective 5.3 - Coming Soon**
- **Status:** Under development by Eya
- **Expected:** Additional 6G network slicing capabilities

### 5G Network Slicing — Friend's Dataset (🟢 Teal)

**Objectives A, B, C - Coming Soon**
- **Status:** To be filled by teammate
- **Expected:** 5G network slicing objectives

## 🔄 Demo Mode

The dashboard runs in **demo mode** when model files are not found:
- ⚠️ Warning banner indicates demo mode
- Realistic mock predictions are generated
- Full UI functionality available for testing
- Easy transition to real models when ready

## 🛠️ How to Replace Models with Real `.joblib` Files

### For Eya (6G Objectives):

1. **Train your models** using your 6G dataset
2. **Save as joblib files:**
   ```python
   import joblib
   joblib.dump(your_model, 'models/model_6G_5_1_xgboost.joblib')
   joblib.dump(your_model, 'models/model_6G_5_2_xgboost.joblib')
   ```
3. **Place in `models/` folder** - the dashboard will automatically detect and use them

### For Friend (5G Objectives):

1. **Train your models** using your 5G dataset
2. **Save as joblib files:**
   ```python
   import joblib
   joblib.dump(your_model, 'models/model_5G_A.joblib')
   joblib.dump(your_model, 'models/model_5G_B.joblib')
   joblib.dump(your_model, 'models/model_5G_C.joblib')
   ```
3. **Update the corresponding page files** to implement your prediction logic

## 📝 How to Add Your Objective (For Teammates)

### Step 1: Update Your Page File
Edit your placeholder page (e.g., `pages/04_5G_objective_A.py`):
- Replace "Coming Soon" content with your implementation
- Follow the structure of `01_6G_objective_5_1.py` as a template
- Add input forms for your required features
- Implement result display with business recommendations

### Step 2: Add Prediction Logic
Update `utils/predict.py`:
```python
def predict_5g_A(model, features, is_demo_mode):
    if is_demo_mode or model is None:
        # Generate realistic mock prediction
        return mock_result
    else:
        # Use real model for prediction
        prediction = model.predict(prepared_features)
        return real_result
```

### Step 3: Add Your Model File
```bash
# Save your trained model
cp your_trained_model.joblib models/model_5G_A.joblib
```

### Step 4: Update Main Page
Update `app.py` to reflect your objective's details in the home page cards.

## 🎨 UI/UX Features

- **Color-coded navigation:** Purple for 6G, Teal for 5G
- **Professional design:** Clean Streamlit interface with custom CSS
- **Business recommendations:** Actionable insights for network operators
- **Interactive visualizations:** Plotly charts for probability gauges and distributions
- **Responsive layout:** Works on desktop and mobile devices
- **Real-time predictions:** Instant ML model inference

## 📊 Model Performance

### 6G Objective 5.1 - Congestion Classification
- **Accuracy:** 97.75%
- **F1-Score:** 0.9775 (weighted)
- **Precision:** 97.75%
- **Recall:** 97.75%
- **Cross-validation:** Stable across 5 folds (std < 0.01)

### 6G Objective 5.2 - QoS Probability Regression
- **R² Score:** 0.8537
- **RMSE:** 0.0162
- **MAE:** [Available in trained model]
- **Training efficiency:** Fast inference suitable for real-time applications

## 🔧 Technical Stack

- **Frontend:** Streamlit 1.28+
- **ML Models:** scikit-learn, XGBoost
- **Visualization:** Plotly
- **Model Storage:** joblib
- **Data Processing:** pandas, numpy
- **Python:** 3.10+

## 🚀 Deployment Options

### Local Development
```bash
streamlit run app.py
```

### Production Deployment
```bash
# Option 1: Streamlit Cloud
# Deploy directly to Streamlit Cloud

# Option 2: Docker
docker build -t network-slicing-dashboard .
docker run -p 8501:8501 network-slicing-dashboard

# Option 3: Traditional hosting
# Use gunicorn + nginx for production deployment
```

## 📈 Future Enhancements

- **Real-time data streaming** from network monitoring systems
- **Historical performance tracking** and trend analysis
- **Automated alert system** for critical predictions
- **Multi-tenant support** for different network operators
- **API endpoints** for integration with existing network management systems
- **Advanced analytics** dashboard for model performance monitoring

## 🤝 Contributing

1. **Fork the repository**
2. **Create a feature branch:** `git checkout -b feature/new-objective`
3. **Add your model and update code**
4. **Test thoroughly:** `streamlit run app.py`
5. **Submit a pull request**

## 📞 Support

For questions or support:
- **Eya (6G objectives):** Contact for 6G network slicing questions
- **Friend (5G objectives):** Contact for 5G network slicing questions
- **Technical issues:** Check model files and dependencies first

## 📄 License

This project is part of the Network Slicing Intelligence initiative for 5G & 6G networks.

---

**Built with ❤️ for network operators and ML engineers**
