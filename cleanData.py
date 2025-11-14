import pandas as pd

# Load your filled dataset
df = pd.read_csv("jharkhand_crops_filled_int.csv")

# Exclude last column (assuming it is crop name or non-numeric)
numeric_cols = df.select_dtypes(include='number').columns[:-1]

# Calculate averages for these columns
column_averages = df[numeric_cols].mean()

# Print results
print("📊 Average values for each numeric column (excluding last):\n")
for col, avg in column_averages.items():
    print(f"{col}: {avg}")