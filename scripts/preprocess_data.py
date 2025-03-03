import pandas as pd
import os
import argparse
from pathlib import Path

def preprocess_cocktails(input_path, output_path):
    """
    Preprocess the cocktails dataset for better usage in the application
    """
    print(f"Reading data from {input_path}")
    df = pd.read_csv(input_path)
    
    # Print initial info
    print(f"Original dataset has {len(df)} rows and {len(df.columns)} columns")
    
    # Check for missing values in important columns
    print("\nMissing values in key columns:")
    for col in ['name', 'category', 'alcoholic', 'glassType', 'instructions']:
        if col in df.columns:
            print(f"{col}: {df[col].isna().sum()} missing values")
    
    # Clean and standardize the data
    
    # 1. Remove unnecessary columns
    columns_to_keep = ['id', 'name', 'category', 'alcoholic', 
                       'glassType', 'instructions']
    
    # Add ingredient and measure columns
    for i in range(1, 16):  # Assuming up to 15 ingredients
        columns_to_keep.append(f'ingredient{i}')
        columns_to_keep.append(f'ingredientMeasure{i}')
    
    # Filter columns that exist in the DataFrame
    columns_to_keep = [col for col in columns_to_keep if col in df.columns]
    df = df[columns_to_keep]
    
    # 2. Clean up ingredient and measure columns
    for i in range(1, 16):
        ing_col = f'ingredient{i}'
        measure_col = f'ingredientMeasure{i}'
        
        if ing_col in df.columns:
            # Replace NaN with empty string
            df[ing_col] = df[ing_col].fillna('').str.strip()
            
        if measure_col in df.columns:
            # Replace NaN with empty string
            df[measure_col] = df[measure_col].fillna('').str.strip()
    
    # 3. Combine ingredients and measurements into a single column for better readability
    ingredient_cols = [f'ingredient{i}' for i in range(1, 16)]
    measure_cols = [f'ingredientMeasure{i}' for i in range(1, 16)]
    
    for i in range(len(ingredient_cols)):
        ing_col = ingredient_cols[i]
        measure_col = measure_cols[i]
        
        if ing_col in df.columns and measure_col in df.columns:
            # Combine ingredient and measure into one column
            df[ing_col] = df.apply(lambda row: f"{row[measure_col]} {row[ing_col]}" if row[ing_col] and row[measure_col] else row[ing_col], axis=1)
            # Drop the measure column after combining
            df.drop(columns=[measure_col], inplace=True)
    
    # 4. Add a simplified alcoholic flag
    if 'alcoholic' in df.columns:
        df['isAlcoholic'] = df['alcoholic'].apply(lambda x: x == 'Alcoholic' if pd.notna(x) else False)
    
    # Save processed data
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"\nPreprocessed data saved to {output_path}")
    print(f"Final dataset has {len(df)} rows and {len(df.columns)} columns")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Preprocess cocktails dataset')
    parser.add_argument('--input', type=str, default='data/cocktails_original.csv',
                        help='Path to input CSV file')
    parser.add_argument('--output', type=str, default='data/cocktails.csv',
                        help='Path to output processed CSV file')
    
    args = parser.parse_args()
    preprocess_cocktails(args.input, args.output)
