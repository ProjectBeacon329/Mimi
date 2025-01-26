import pandas as pd
import logging
import requests
from io import StringIO

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def calculate_cost_per_batch(ingredients, recipe, batch_size=12):
    """Calculate the cost per batch of items."""
    # Validate batch size
    if batch_size <= 0:
        raise ValueError(f"Batch size must be positive. Got: {batch_size}")
    
    total_cost = 0
    
    # Calculate cost for each ingredient in the recipe
    for index, row in recipe.iterrows():
        ingredients_name = row['Item']
        quantity = row['Quantity Needed']
        
        # Check if ingredient exists in ingredients DataFrame
        if not any(ingredients['Item'] == ingredients_name):
            raise ValueError(f"Ingredient '{ingredients_name}' not found in ingredients data")
        
        try:
            # Get the cost per unit from ingredients DataFrame
            cost_per_unit = ingredients.loc[ingredients['Item'] == ingredients_name, 'Unit Cost'].iloc[0]
            # Remove '$' and convert to float
            cost_per_unit = float(cost_per_unit.replace('$', ''))
            # Calculate cost for this ingredient
            ingredient_cost = cost_per_unit * quantity
            total_cost += ingredient_cost
        except Exception as e:
            print(f"Error processing ingredient '{ingredients_name}': {str(e)}")
            raise
    
    # Calculate cost per item
    cost_per_item = total_cost / batch_size
    
    return {
        'total_batch_cost': round(total_cost, 2),
        'cost_per_item': round(cost_per_item, 2)
    }

def suggest_price(cost_per_item, margin=3.00):
    """Calculate the suggested selling price."""
    if margin <= 0:
        raise ValueError("Margin must be greater than 0")
    
    price = cost_per_item * (1 + margin)
    return round(price, 2)

def perform_sensitivity_analysis(ingredients_data, recipe_requirements, batch_size=12, 
                              cost_variations=[0.8, 0.9, 1.0, 1.1, 1.2], 
                              size_variations=[6, 12, 24, 36]):
    """Perform sensitivity analysis on costs and batch sizes."""
    results = {
        'cost_sensitivity': {},
        'batch_size_sensitivity': {}
    }
    
    # Cost sensitivity analysis
    for variation in cost_variations:
        # Create a copy of ingredients data to modify
        modified_ingredients = ingredients_data.copy()
        # Modify the Unit Cost column
        modified_ingredients['Unit Cost'] = modified_ingredients['Unit Cost'].apply(
            lambda x: f"${float(x.replace('$', '')) * variation}"
        )
        
        try:
            costs = calculate_cost_per_batch(modified_ingredients, recipe_requirements, batch_size)
            results['cost_sensitivity'][f"{int(variation * 100)}%"] = {
                'cost_per_item': costs['cost_per_item'],
                'suggested_price': suggest_price(costs['cost_per_item'])
            }
        except Exception as e:
            results['cost_sensitivity'][f"{int(variation * 100)}%"] = f"Error: {str(e)}"
    
    # Batch size sensitivity analysis
    for size in size_variations:
        try:
            costs = calculate_cost_per_batch(ingredients_data, recipe_requirements, size)
            results['batch_size_sensitivity'][size] = {
                'cost_per_item': costs['cost_per_item'],
                'suggested_price': suggest_price(costs['cost_per_item'])
            }
        except Exception as e:
            results['batch_size_sensitivity'][size] = f"Error: {str(e)}"
    
    return results

class CostModel:
    def __init__(self, ingredients_source, recipe_source=None, is_url=False, default_batch_size=12, default_margin=3.00):
        """
        Initialize the cost model with data and default values.
        
        Args:
            ingredients_source: Either a file path or StringIO object containing ingredients data
            recipe_source: Either a file path or URL to recipe data
            is_url (bool): If True, sources are treated as URLs
            default_batch_size (int): Default batch size for calculations
            default_margin (float): Default margin for price calculations
        """
        self.default_batch_size = default_batch_size
        self.default_margin = default_margin
        self.session = requests.Session()
        self.session.headers.update({
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        })
        
        try:
            if is_url and isinstance(ingredients_source, str):
                response = self.session.get(ingredients_source)
                if response.status_code != 200:
                    raise Exception(f"Failed to fetch ingredients data: HTTP {response.status_code}")
                ingredients_data = StringIO(response.text)
                self.ingredients_df = pd.read_csv(ingredients_data, skipinitialspace=True)
            else:
                self.ingredients_df = pd.read_csv(ingredients_source, skipinitialspace=True)
            logging.info("Successfully loaded ingredients data")
            
            if recipe_source:
                if is_url:
                    response = self.session.get(recipe_source)
                    if response.status_code != 200:
                        raise Exception(f"Failed to fetch recipe data: HTTP {response.status_code}")
                    recipe_data = StringIO(response.text)
                    self.recipe_df = pd.read_csv(recipe_data, skipinitialspace=True)
                else:
                    self.recipe_df = pd.read_csv(recipe_source, skipinitialspace=True)
                logging.info("Successfully loaded recipe data")
        except Exception as e:
            logging.error(f"Error loading data: {str(e)}")
            raise

    def calculate_recipe_costs(self, recipe_path):
        """Calculate costs for a specific recipe."""
        try:
            if recipe_path.startswith('http'):
                response = self.session.get(recipe_path)
                if response.status_code != 200:
                    raise Exception(f"Failed to fetch recipe data: HTTP {response.status_code}")
                recipe_data = StringIO(response.text)
                recipe_df = pd.read_csv(recipe_data, skipinitialspace=True)
            else:
                recipe_df = pd.read_csv(recipe_path, skipinitialspace=True)
            logging.info(f"Successfully loaded recipe from {recipe_path}")
            
            costs = calculate_cost_per_batch(self.ingredients_df, recipe_df, self.default_batch_size)
            suggested_price = suggest_price(costs['cost_per_item'], self.default_margin)
            
            logging.info("Cost calculation completed successfully")
            return {
                'costs': costs,
                'suggested_price': suggested_price
            }
        except Exception as e:
            logging.error(f"Error calculating recipe costs: {str(e)}")
            raise

    def run_sensitivity_analysis(self, recipe_path):
        """Run sensitivity analysis on the recipe."""
        try:
            if recipe_path.startswith('http'):
                response = self.session.get(recipe_path)
                if response.status_code != 200:
                    raise Exception(f"Failed to fetch recipe data: HTTP {response.status_code}")
                recipe_data = StringIO(response.text)
                recipe_df = pd.read_csv(recipe_data, skipinitialspace=True)
            else:
                recipe_df = pd.read_csv(recipe_path, skipinitialspace=True)
            sensitivity_results = perform_sensitivity_analysis(
                self.ingredients_df, 
                recipe_df
            )
            logging.info("Sensitivity analysis completed successfully")
            return sensitivity_results
        except Exception as e:
            logging.error(f"Error in sensitivity analysis: {str(e)}")
            raise

    def print_analysis(self, recipe_path):
        """Print comprehensive cost analysis."""
        try:
            # Calculate basic costs
            results = self.calculate_recipe_costs(recipe_path)
            print("\nBasic Cost Analysis:")
            print(f"Total Batch Cost: ${results['costs']['total_batch_cost']}")
            print(f"Cost per Item: ${results['costs']['cost_per_item']}")
            print(f"Suggested Selling Price: ${results['suggested_price']}")

            # Run and print sensitivity analysis
            sensitivity = self.run_sensitivity_analysis(recipe_path)
            
            print("\nSensitivity Analysis:")
            print("\nCost Variations (at standard batch size):")
            for cost_var, results in sensitivity['cost_sensitivity'].items():
                print(f"At {cost_var} of base cost:")
                print(f"  Cost per Item: ${results['cost_per_item']}")
                print(f"  Suggested Price: ${results['suggested_price']}")
            
            print("\nBatch Size Variations:")
            for size, results in sensitivity['batch_size_sensitivity'].items():
                print(f"With batch size of {size}:")
                print(f"  Cost per Item: ${results['cost_per_item']}")
                print(f"  Suggested Price: ${results['suggested_price']}")

        except Exception as e:
            logging.error(f"Error in analysis printing: {str(e)}")
            raise

def main():
    # GitHub raw file URLs
    ingredients_url = "https://raw.githubusercontent.com/ProjectBeacon329/Project-Mercury/refs/heads/main/ingredients.csv"
    recipe_url = "https://raw.githubusercontent.com/ProjectBeacon329/Project-Mercury/refs/heads/main/recipe.csv"
    
    try:
        model = CostModel(ingredients_url, recipe_url, is_url=True)
        model.print_analysis(recipe_url)
    except Exception as e:
        logging.error(f"Main execution failed: {str(e)}")

if __name__ == "__main__":
    main() 