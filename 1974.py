import pandas as pd

# Read the CSV files with comma delimiter instead of pipe
ingredients_df = pd.read_csv(r'C:\Users\adamy\OneDrive\Desktop\Project Mercury\Data\ingredients.csv', skipinitialspace=True)
recipe_df = pd.read_csv(r'C:\Users\adamy\OneDrive\Desktop\Project Mercury\Data\recipe.csv', skipinitialspace=True)

# Debug: Print column names
print("\nIngredients DataFrame columns:", ingredients_df.columns.tolist())
print("\nRecipe DataFrame columns:", recipe_df.columns.tolist())
print("\nFirst few rows of ingredients_df:")
print(ingredients_df.head())
print("\nFirst few rows of recipe_df:")
print(recipe_df.head())

def calculate_cost_per_batch(ingredients, recipe, batch_size=12):
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
    """
    Calculate the minimum viable selling price based on cost and desired profit margin.
    
    Args:
        cost_per_item (float): Cost to produce one item
        margin (float): Desired profit margin as a decimal (default 3.00 for 300%)
    
    Returns:
        float: Suggested selling price rounded to 2 decimal places
    """
    if margin <= 0:
        raise ValueError("Margin must be greater than 0")
    
    price = cost_per_item * (1 + margin)
    return round(price, 2)

def perform_sensitivity_analysis(ingredients_data, recipe_requirements, batch_size=12, 
                              cost_variations=[0.8, 0.9, 1.0, 1.1, 1.2], 
                              size_variations=[6, 12, 24, 36]):
    """
    Perform sensitivity analysis on costs and batch sizes.
    
    Args:
        ingredients_data (DataFrame): Original ingredients data
        recipe_requirements (DataFrame): Recipe requirements
        batch_size (int): Default batch size
        cost_variations (list): List of multipliers for cost variation
        size_variations (list): List of different batch sizes to test
    
    Returns:
        dict: Nested dictionary containing analysis results
    """
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

try:
    # Calculate costs
    costs = calculate_cost_per_batch(ingredients_df, recipe_df)
    
    # Calculate suggested price
    suggested_price = suggest_price(costs['cost_per_item'])
    
    print("\nCost Breakdown:")
    print(f"Total Batch Cost: ${costs['total_batch_cost']}")
    print(f"Cost per Item: ${costs['cost_per_item']}")
    print(f"Suggested Selling Price: ${suggested_price}")
    
    # Perform sensitivity analysis
    sensitivity_results = perform_sensitivity_analysis(ingredients_df, recipe_df)
    
    print("\nSensitivity Analysis:")
    print("\nCost Variations (at standard batch size):")
    for cost_var, results in sensitivity_results['cost_sensitivity'].items():
        print(f"At {cost_var} of base cost:")
        print(f"  Cost per Item: ${results['cost_per_item']}")
        print(f"  Suggested Price: ${results['suggested_price']}")
    
    print("\nBatch Size Variations:")
    for size, results in sensitivity_results['batch_size_sensitivity'].items():
        print(f"With batch size of {size}:")
        print(f"  Cost per Item: ${results['cost_per_item']}")
        print(f"  Suggested Price: ${results['suggested_price']}")
    
except ValueError as ve:
    print(f"Validation Error: {str(ve)}")
except Exception as e:
    print(f"An unexpected error occurred: {str(e)}")
