# XGBoost Malware Detection API

A Flask-based web service that uses XGBoost and EMBER features to classify Windows PE executables as malicious or benign.

## Overview

This project implements a machine learning pipeline that:
1. Extracts 2381-dimensional feature vectors from PE files using EMBER
2. Trains an XGBoost classifier on pre-processed feature data
3. Serves predictions via a REST API that returns only binary labels

## Architecture

- **Feature Extraction**: EMBER (Elastic Malware Benchmark) extracts static PE features
- **Model**: XGBoost binary classifier trained on 4M+ samples
- **API**: Flask server with `/predict` endpoint accepting file uploads
- **Output**: Returns only `{"label": 0|1}` (0=benign, 1=malicious)

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Download Training Data (Optional - for retraining)

The feature files are not included in the repository due to size. Download them using AWS CLI if you want to retrain the model:

```bash
# Install AWS CLI if not already installed
pip install awscli

# Download training features (4.2M samples, ~2GB)
aws s3 cp s3://your-bucket/defender/models/features/test-features.npz defender/models/features/

# Download validation features (2.5M samples, ~1.2GB)  
aws s3 cp s3://your-bucket/defender/models/features/validation-features.npz defender/models/features/
```

### 3. Train the Model (Optional - pre-trained model included)

A pre-trained model is included in the repository. To retrain:

```bash
python defender/models/train_xgb.py
```

This will:
- Load training data from `test-features.npz` (subsampled to 150k samples)
- Load validation data from `validation-features.npz` (subsampled to 100k samples)
- Train XGBoost with early stopping
- Save model to `defender/models/xgb_model.json`
- Print validation metrics (accuracy, precision, recall, F1, FPR, TPR)

### 4. Run the Server

```bash
python -m defender
```

Server starts on `http://localhost:8000`

## API Usage

### Health Check
```bash
curl http://localhost:8000/health
```

### Predict Malware
```bash
# Upload a PE file for classification
curl -F "file=@path/to/executable.exe" http://localhost:8000/predict

# Response: {"label": 0} or {"label": 1}
```

## Docker Deployment

### Build Image
```bash
docker build -t xgboost-malware-detector .
```

### Run Container
```bash
docker run -p 8000:8000 xgboost-malware-detector
```

## File Structure

```
├── defender/
│   ├── __main__.py              # Flask server
│   ├── inference_service.py     # Feature extraction + scoring
│   └── models/
│       ├── train_xgb.py         # Training script
│       ├── predict_xgb.py       # Model loader/predictor
│       ├── xgb_model.json       # Trained model (generated)
│       └── features/            # Training data (download required)
│           ├── test-features.npz
│           └── validation-features.npz
├── requirements.txt             # Python dependencies
├── Dockerfile                   # Container definition
└── README.md                   # This file
```

## Model Performance

The XGBoost model achieves:
- **Validation Accuracy**: ~97.6%
- **Validation Precision**: ~97.4%
- **Validation Recall**: ~96.4%
- **Validation F1**: ~96.9%
- **False Positive Rate**: ~1.6%
- **True Positive Rate**: ~96.4%

## Dependencies

- **Flask**: Web framework
- **XGBoost**: Machine learning model
- **EMBER**: PE feature extraction
- **LIEF**: PE file parsing
- **NumPy/SciKit-Learn**: Numerical operations
- **Pandas**: Data manipulation

## Notes

- The API returns only binary labels to avoid exposing model internals
- Feature extraction applies compatibility shims for numpy/lief/sklearn
- Training uses subsampling to manage memory usage
- Model supports early stopping and best iteration selection