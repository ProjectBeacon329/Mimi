from flask import Flask, request, jsonify
import pandas as pd
from cost_model import CostModel
import logging
import os

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)

# Initialize the cost model with ingredients data
INGREDIENTS_PATH = r'C:\Users\adamy\OneDrive\Desktop\Project Mercury\Data\ingredients.csv'
cost_model = None

try:
    cost_model = CostModel(INGREDIENTS_PATH)
    logging.info("Cost model initialized successfully")
except Exception as e:
    logging.error(f"Failed to initialize cost model: {str(e)}")

@app.route('/calculate-cost', methods=['POST'])
def calculate_cost():
    """
    Calculate cost based on recipe requirements and batch size.
    Expected JSON format:
    {
        "recipe_requirements": {
            "Item1": quantity1,
            "Item2": quantity2,
            ...
        },
        "batch_size": number
    }
    """
    try:
        # Get JSON data from request
        data = request.get_json()
        
        if not data or 'recipe_requirements' not in data:
            return jsonify({'error': 'Missing recipe requirements'}), 400
        
        # Convert recipe requirements to DataFrame
        recipe_data = pd.DataFrame([
            {'Item': item, 'Quantity Needed': qty}
            for item, qty in data['recipe_requirements'].items()
        ])
        
        # Get batch size from request or use default
        batch_size = data.get('batch_size', 12)
        
        # Calculate costs using the cost model
        costs = cost_model.calculate_cost_per_batch(cost_model.ingredients_df, recipe_data, batch_size)
        suggested_price = cost_model.suggest_price(costs['cost_per_item'])
        
        # Prepare response
        response = {
            'total_batch_cost': costs['total_batch_cost'],
            'cost_per_item': costs['cost_per_item'],
            'suggested_price': suggested_price,
            'batch_size': batch_size
        }
        
        logging.info(f"Successfully calculated costs for recipe with {len(recipe_data)} ingredients")
        return jsonify(response)
    
    except ValueError as ve:
        logging.error(f"Validation error: {str(ve)}")
        return jsonify({'error': str(ve)}), 400
    except Exception as e:
        logging.error(f"Error calculating costs: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint"""
    return jsonify({'status': 'healthy', 'ingredients_loaded': cost_model is not None})

if __name__ == '__main__':
    app.run(debug=True, port=5000) 