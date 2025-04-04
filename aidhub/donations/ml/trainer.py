import joblib
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.neighbors import KNeighborsRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression
import logging
from django.conf import settings
from django.db.models import Count
from ..models import Recipient, DonatedRecipient, Donation
import os

logger = logging.getLogger('aidhub')

MODEL_FILE = os.path.join(settings.BASE_DIR, 'donations/ml/models/donation_matcher.pkl')
TREND_MODEL_FILE = os.path.join(settings.BASE_DIR, 'donations/ml/models/trend_predictor.pkl')

def get_combined_dataset():
    # Get current recipients
    current_data = pd.DataFrame(
        Recipient.objects.all().values(
            'id', 'name', 'location', 'latitude', 'longitude', 
            'donation_type', 'urgency', 'date_added'
        )
    )
    
    # Get historical data
    historical_data = pd.DataFrame(
        DonatedRecipient.objects.all().values(
            'id', 'name', 'location', 'latitude', 'longitude',
            'donation_type', 'urgency', 'transaction_date'
        )
    ).rename(columns={'transaction_date': 'date_added'})
    
    # Combine datasets
    df = pd.concat([current_data, historical_data], ignore_index=True)
    
    if len(df) == 0:
        return None, None, None, []
    
    # Print dataset statistics
    logger.info(f"Training on {len(df)} total data points")
    logger.info(f"Donation types: {df['donation_type'].value_counts().to_dict()}")
    
    # Features for prediction
    X = pd.DataFrame()
    X['latitude'] = df['latitude']
    X['longitude'] = df['longitude']
    
    # Convert donation_type to categorical codes
    donation_types = pd.Categorical(df['donation_type'])
    X['donation_type_code'] = donation_types.codes
    
    # One-hot encode donation types
    donation_dummies = pd.get_dummies(df['donation_type'], prefix='type')
    X = pd.concat([X, donation_dummies], axis=1)
    
    # Add time-based features
    df['date_added'] = pd.to_datetime(df['date_added'])
    X['day_of_week'] = df['date_added'].dt.dayofweek
    X['day_of_month'] = df['date_added'].dt.day
    X['month'] = df['date_added'].dt.month
    
    # Target variable
    y = df['urgency']
    
    return df, X, y, donation_types.categories.tolist()

def train_model():
    try:
        df, X, y, donation_categories = get_combined_dataset()
        
        if df is None or len(df) < 1:
            logger.warning("No data available to train the model.")
            return None
        
        logger.info(f"Training model with {len(df)} data points...")
        
        # Choose model based on data size
        if len(df) < 5:
            model = KNeighborsRegressor(n_neighbors=min(3, len(df)))
        elif len(df) < 15:
            model = LinearRegression()
        else:
            model = RandomForestRegressor(n_estimators=100, random_state=42)
        
        # Scale features
        scaler = StandardScaler()
        numeric_features = ['latitude', 'longitude', 'day_of_week', 'day_of_month', 'month']
        X_scaled = X.copy()
        X_scaled[numeric_features] = scaler.fit_transform(X[numeric_features])
        
        # Train model
        if len(df) >= 5:
            X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2)
            model.fit(X_train, y_train)
            score = model.score(X_test, y_test)
            logger.info(f"Model R² score: {score:.4f}")
        else:
            model.fit(X_scaled, y)
        
        # Save model data
        model_data = {
            'model': model,
            'donation_categories': donation_categories,
            'scaler': scaler,
            'numeric_features': numeric_features
        }
        
        os.makedirs(os.path.dirname(MODEL_FILE), exist_ok=True)
        joblib.dump(model_data, MODEL_FILE)
        logger.info("Model saved successfully")
        
        return model_data
        
    except Exception as e:
        logger.error(f"Error in train_model: {e}")
        return None

def train_trend_model():
    try:
        # Get all donation data
        recipients = pd.DataFrame(
            Recipient.objects.values('donation_type', 'date_added')
        )
        donated = pd.DataFrame(
            DonatedRecipient.objects.values('donation_type', 'transaction_date')
        ).rename(columns={'transaction_date': 'date_added'})
        donations = pd.DataFrame(
            Donation.objects.values('donation_type', 'donation_date')
        ).rename(columns={'donation_date': 'date_added'})
        
        all_data = pd.concat([recipients, donated, donations], ignore_index=True)
        
        if len(all_data) < 3:
            logger.warning("Not enough data to train trend model")
            return None
            
        # Process data
        all_data['date_added'] = pd.to_datetime(all_data['date_added'])
        all_data['date'] = all_data['date_added'].dt.date
        grouped = all_data.groupby(['donation_type', 'date']).size().reset_index(name='count')
        
        # Train models for each donation type
        trend_models = {}
        for dtype in all_data['donation_type'].unique():
            type_data = grouped[grouped['donation_type'] == dtype]
            if len(type_data) < 3:
                continue
                
            # Create features
            type_data['date'] = pd.to_datetime(type_data['date'])
            X = pd.DataFrame({
                'day_of_week': type_data['date'].dt.dayofweek,
                'day_of_month': type_data['date'].dt.day,
                'month': type_data['date'].dt.month
            })
            
            # Train model
            model = LinearRegression()
            model.fit(X, type_data['count'])
            trend_models[dtype] = model
        
        # Save trend models
        os.makedirs(os.path.dirname(TREND_MODEL_FILE), exist_ok=True)
        joblib.dump(trend_models, TREND_MODEL_FILE)
        logger.info(f"Trained trend models for {len(trend_models)} donation types")
        
        return trend_models
        
    except Exception as e:
        logger.error(f"Error training trend model: {e}")
        return None
