# Credit Card Fraud Detection System

## Project Overview
The Credit Card Fraud Detection System is a machine learning-based web application designed to identify potentially fraudulent credit card transactions. It helps users detect suspicious transactions using a trained machine learning model.

## Technologies Used
- Python
- Flask
- Machine Learning
- Random Forest Classifier
- HTML
- CSS
- MySQL

## Features
- User Registration and Login
- Credit Card Fraud Prediction
- Fraud Probability Estimation
- Transaction History
- Admin Login and Dashboard
- Fraud Alerts and Monitoring

## Project Structure
```text
CreditCardFraudDetection/
│
├── model/
├── static/
├── templates/
├── app.py
├── fraud_model.pkl
└── feature_columns.pkl
```

## Dataset
The project uses a credit card transaction dataset for training and testing the machine learning model.

**Note:** The original CSV dataset is not included in this repository because of its large file size. Place the dataset in the required location before running the application.

## Installation and Setup

1. Clone the repository:
```bash
git clone https://github.com/aneettta-as/CreditCardFraudDetection.git
```

2. Open the project folder:
```bash
cd CreditCardFraudDetection
```

3. Install the required dependencies:
```bash
pip install -r requirements.txt
```

4. Ensure the required dataset and model files are available.

5. Run the application:
```bash
python app.py
```

6. Open your browser and visit:
```text
http://127.0.0.1:5000
```

## Project Objective
To develop an intelligent fraud detection system that helps identify suspicious credit card transactions using machine learning techniques.

## Author
Credit Card Fraud Detection Project
