# XGBoost Malware Detection System

A production-ready machine learning system that classifies Windows PE executables as malicious or benign using XGBoost and EMBER feature extraction. Includes both local and Docker deployment options with comprehensive testing capabilities.

## 🚀 Quick Start

### Docker (Recommended)
```bash
# Build and run the container
docker build -t xgboost-malware-detector .
docker run -d -p 8080:8080 --name malware-detector xgboost-malware-detector

# Test with a file
curl -X POST -H "Content-Type: application/octet-stream" --data-binary "@file.exe" http://localhost:8080/

# Run full test suite
python test_docker.py
```

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
python -m defender

# Test locally
python test_local.py
```

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Installation](#installation)
- [Usage](#usage)
- [Testing](#testing)
- [Docker Deployment](#docker-deployment)
- [API Reference](#api-reference)
- [Model Performance](#model-performance)
- [File Structure](#file-structure)
- [Troubleshooting](#troubleshooting)

## 🎯 Overview

This system provides a robust malware detection API that:

- **Extracts 2,381 features** from PE files using EMBER (Elastic Malware Benchmark)
- **Uses XGBoost** for binary classification (malicious vs benign)
- **Serves predictions** via REST API in competition format
- **Supports both local and containerized deployment**
- **Includes comprehensive testing tools**

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   PE File       │───▶│  EMBER Feature   │───▶│  XGBoost Model  │
│   (Binary)      │    │  Extraction      │    │  Classification │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
                                                         ▼
                                                ┌─────────────────┐
                                                │  JSON Response  │
                                                │  {"result": 0|1}│
                                                └─────────────────┘
```

### Components

- **Feature Extraction**: EMBER extracts static PE features (imports, exports, sections, etc.)
- **Model**: XGBoost binary classifier trained on 4M+ samples
- **API**: Flask server with competition-compliant endpoints
- **Compatibility**: Runtime fixes for EMBER/LIEF compatibility across environments

## 📦 Installation

### Prerequisites

- Python 3.9+
- Docker (optional, for containerized deployment)
- 4GB+ RAM (for feature extraction)

### Local Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd CSCE439Group3
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Verify installation**
   ```bash
   python -c "from defender.inference_service import score_exe; print('✅ Installation successful')"
   ```

### Docker Installation

1. **Build the image**
   ```bash
   docker build -t xgboost-malware-detector .
   ```

2. **Run the container**
   ```bash
   docker run -d -p 8080:8080 --name malware-detector xgboost-malware-detector
   ```

3. **Verify deployment**
   ```bash
   curl -X POST -H "Content-Type: application/octet-stream" http://localhost:8080/
   ```

## 🚀 Usage

### Local Server

```bash
# Start the server
python -m defender

# Server runs on http://localhost:8080
```

### Docker Server

```bash
# Start container
docker run -d -p 8080:8080 --name malware-detector xgboost-malware-detector

# Check status
docker ps
docker logs malware-detector
```

### API Calls

#### PowerShell (Windows)
```powershell
Invoke-RestMethod -Uri "http://localhost:8080/" -Method Post -ContentType "application/octet-stream" -InFile "file.exe"
```

#### Bash/Linux
```bash
curl -X POST -H "Content-Type: application/octet-stream" --data-binary "@file.exe" http://localhost:8080/
```

#### Python
```python
import requests

with open('file.exe', 'rb') as f:
    response = requests.post(
        'http://localhost:8080/',
        data=f,
        headers={'Content-Type': 'application/octet-stream'}
    )
    print(response.json())  # {"result": 0} or {"result": 1}
```

## 🧪 Testing

### Automated Test Suites

#### Docker Testing
```bash
# Run comprehensive test suite against Docker container
python test_docker.py
```

#### Local Testing
```bash
# Run tests against local inference service
python test_local.py
```

### Manual Testing

#### Single File Test
```bash
# Test a specific file
curl -X POST -H "Content-Type: application/octet-stream" --data-binary "@suspicious.exe" http://localhost:8080/
```

#### Health Check
```bash
# Check if service is running
curl -X POST -H "Content-Type: application/octet-stream" http://localhost:8080/
```

### Test Data Structure

The test scripts expect the following directory structure:
```
challenge_ds/
├── malware/
│   ├── 1/
│   ├── 2/
│   └── ...
└── goodware/
    ├── 1/
    ├── 2/
    └── ...
```

## 🐳 Docker Deployment

### Build Commands
```bash
# Build image
docker build -t xgboost-malware-detector .

# Build with no cache (if issues)
docker build --no-cache -t xgboost-malware-detector .
```

### Run Commands
```bash
# Run in background
docker run -d -p 8080:8080 --name malware-detector xgboost-malware-detector

# Run interactively
docker run -it -p 8080:8080 --name malware-detector xgboost-malware-detector

# Run with custom port
docker run -d -p 9000:8080 --name malware-detector xgboost-malware-detector
```

### Management Commands
```bash
# Check status
docker ps
docker logs malware-detector

# Stop and remove
docker stop malware-detector
docker rm malware-detector

# Remove image
docker rmi xgboost-malware-detector
```

## 📡 API Reference

### Endpoints

#### `POST /`
Main prediction endpoint (competition format)

**Request:**
- Method: `POST`
- Content-Type: `application/octet-stream`
- Body: Raw binary data of PE file

**Response:**
```json
{"result": 0}  // 0 = benign, 1 = malicious
```

**Examples:**
```bash
# PowerShell
Invoke-RestMethod -Uri "http://localhost:8080/" -Method Post -ContentType "application/octet-stream" -InFile "file.exe"

# Bash
curl -X POST -H "Content-Type: application/octet-stream" --data-binary "@file.exe" http://localhost:8080/
```

### Response Codes

- `200`: Successful prediction
- `400`: Invalid request (empty data, wrong content type)
- `500`: Internal server error (defaults to benign)

## 📊 Model Performance

The XGBoost model achieves the following performance metrics:

| Metric | Value |
|--------|-------|
| **Validation Accuracy** | ~97.6% |
| **Validation Precision** | ~97.4% |
| **Validation Recall** | ~96.4% |
| **Validation F1-Score** | ~96.9% |
| **False Positive Rate** | ~1.6% |
| **True Positive Rate** | ~96.4% |

### Training Details

- **Training Samples**: 150,000 (subsampled from 4M+)
- **Validation Samples**: 100,000 (subsampled from 2.5M+)
- **Features**: 2,381 EMBER features
- **Model**: XGBoost with early stopping
- **Training Time**: ~5-10 minutes on modern hardware

## 📁 File Structure

```
CSCE439Group3/
├── defender/                          # Main application
│   ├── __main__.py                   # Flask server entry point
│   ├── inference_service.py          # Feature extraction & scoring
│   ├── ember_compat.py               # Runtime compatibility fixes
│   └── models/
│       ├── train_xgb.py              # Model training script
│       ├── predict_xgb.py            # Model prediction
│       ├── xgb_model.json            # Trained model file
│       └── features/                 # Training data (optional)
│           ├── test-features.npz
│           └── validation-features.npz
├── test/                             # Test utilities
│   └── test_ember_compat_runtime.py
├── test_docker.py                    # Docker testing script
├── test_local.py                     # Local testing script
├── requirements.txt                  # Python dependencies
├── docker-requirements.txt           # Docker dependencies
├── Dockerfile                        # Container definition
└── README.md                         # This file
```

## 🔧 Troubleshooting

### Common Issues

#### Docker Issues

**Container won't start:**
```bash
# Check logs
docker logs malware-detector

# Check port availability
netstat -an | grep 8080

# Rebuild with no cache
docker build --no-cache -t xgboost-malware-detector .
```

**Port already in use:**
```bash
# Use different port
docker run -d -p 9000:8080 --name malware-detector xgboost-malware-detector

# Or stop existing container
docker stop malware-detector
```

#### Local Installation Issues

**Import errors:**
```bash
# Reinstall dependencies
pip install --force-reinstall -r requirements.txt

# Check Python path
python -c "import sys; print(sys.path)"
```

**EMBER compatibility issues:**
```bash
# The system includes automatic compatibility fixes
# If issues persist, check the ember_compat.py file
```

#### API Issues

**Connection refused:**
```bash
# Check if server is running
curl http://localhost:8080/

# Check firewall settings
# Ensure port 8080 is accessible
```

**Wrong content type:**
```bash
# Ensure you're using application/octet-stream
curl -X POST -H "Content-Type: application/octet-stream" --data-binary "@file.exe" http://localhost:8080/
```

### Performance Optimization

**For large-scale deployment:**
- Use multiple container instances behind a load balancer
- Consider GPU acceleration for XGBoost (requires custom build)
- Implement caching for frequently requested files
- Use connection pooling for database operations

**Memory optimization:**
- The system uses subsampling during training to manage memory
- Feature extraction is optimized for single-file processing
- Consider batch processing for multiple files

## 📝 Development

### Training New Models

#### Download Training Data

The feature files are not included in the repository due to size. Download them using the SOREL-20M dataset which provides pre-extracted EMBER features:

**Method 1: Download from SOREL-20M S3 Bucket (No AWS Account Required)**
```bash
# Install AWS CLI
pip install awscli

# Download pre-extracted EMBER features from SOREL-20M dataset
# These are publicly accessible without AWS credentials
aws s3 cp s3://sorel-20m/09-DEC-2020/lightGBM-features/train-features.npz defender/models/features/test-features.npz --no-sign-request
aws s3 cp s3://sorel-20m/09-DEC-2020/lightGBM-features/validation-features.npz defender/models/features/validation-features.npz --no-sign-request

# Optional: Download test features as well
aws s3 cp s3://sorel-20m/09-DEC-2020/lightGBM-features/test-features.npz defender/models/features/test-features.npz --no-sign-request
```

**Method 2: Direct Download with wget/curl**
```bash
# Alternative download method (if AWS CLI is not available)
# Note: These URLs may need to be verified as they might require S3 access
wget https://sorel-20m.s3.amazonaws.com/09-DEC-2020/lightGBM-features/train-features.npz -O defender/models/features/test-features.npz
wget https://sorel-20m.s3.amazonaws.com/09-DEC-2020/lightGBM-features/validation-features.npz -O defender/models/features/validation-features.npz
```

**Method 3: Using the SOREL-20M Dataset Directly**
```bash
# Clone the SOREL-20M repository for additional tools and utilities
git clone https://github.com/sophos/SOREL-20M.git
cd SOREL-20M

# Use their provided scripts to work with the dataset
# See their README for detailed instructions
```

**Dataset Information:**
- **Source**: [SOREL-20M Dataset](https://github.com/sophos/SOREL-20M) by Sophos and ReversingLabs
- **Size**: ~20 million malware samples with EMBER features
- **Features**: 2,381-dimensional EMBER feature vectors
- **Format**: Pre-extracted `.npz` files ready for training
- **License**: Apache 2.0

**File Sizes:**
- `train-features.npz`: ~113GB
- `validation-features.npz`: ~23GB  
- `test-features.npz`: ~38GB

**Note**: The SOREL-20M dataset contains only malware samples (no benign samples). For a complete training dataset, you may need to combine this with benign samples from other sources.

#### Train the Model
```bash
# Train new model
python defender/models/train_xgb.py

# Model will be saved to defender/models/xgb_model.json
```

### Adding New Features

1. Modify `defender/inference_service.py` for feature extraction
2. Update `defender/models/train_xgb.py` for training
3. Retrain the model with new features
4. Update tests to verify functionality

### Testing Changes

```bash
# Run local tests
python test_local.py

# Run Docker tests
python test_docker.py

# Run unit tests
python -m pytest test/
```

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📞 Support

For issues and questions:
1. Check the troubleshooting section
2. Review the test scripts for usage examples
3. Check Docker logs for container issues
4. Open an issue on the repository

---

**Note**: This system is designed for educational and research purposes. Always follow responsible disclosure practices when working with malware samples.