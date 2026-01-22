"""
Test script to check if CSV data is being read correctly
"""
import pandas as pd
import os


def test_customer_csv():
    """Test reading customer CSV file"""
    try:
        csv_file_path = os.path.join(os.path.dirname(
            __file__), "data", "customer_data.csv")

        print("🔄 Reading customer_data.csv...")
        print("-" * 70)

        # Try reading with different separators
        try:
            df = pd.read_csv(csv_file_path)
            print(f"✅ Successfully read CSV with default comma separator")
        except:
            df = pd.read_csv(csv_file_path, sep='\t')
            print(f"✅ Successfully read CSV with tab separator")

        print(f"\n📊 Total rows: {len(df)}")
        print(f"📊 Total columns: {len(df.columns)}")
        print(f"\n📋 Column names:\n{list(df.columns)}")

        print("\n" + "="*70)
        print("First 3 customer records:")
        print("="*70)

        for idx in range(min(3, len(df))):
            row = df.iloc[idx]
            print(f"\n🧑 Customer {idx+1}:")
            print(f"  ID: {row.get('customer_id', 'N/A')}")
            print(f"  Name: {row.get('customer_name', 'N/A')}")
            print(f"  Phone: {row.get('phone', 'N/A')}")
            print(f"  Address: {row.get('address', 'N/A')}")
            print(f"  Loyalty Points: {row.get('loyalty_points', 'N/A')}")
            print(
                f"  Order History: {str(row.get('order_history', 'N/A'))[:50]}...")
            print(f"  Pending Orders: {row.get('pending_orders', 'N/A')}")

        print("\n" + "="*70)
        print("Checking for data issues:")
        print("="*70)

        # Check for missing values
        missing = df.isnull().sum()
        if missing.sum() > 0:
            print("\n⚠️  Missing values found:")
            for col, count in missing.items():
                if count > 0:
                    print(f"  - {col}: {count} missing")
        else:
            print("\n✅ No missing values")

        # Check for rows with NaN in critical fields
        critical_fields = ['customer_id', 'customer_name']
        invalid_rows = df[df[critical_fields].isnull().any(axis=1)]
        if len(invalid_rows) > 0:
            print(
                f"\n⚠️  {len(invalid_rows)} rows have missing critical data (customer_id or customer_name)")
        else:
            print("\n✅ All rows have valid customer_id and customer_name")

        return True

    except Exception as e:
        print(f"❌ Error reading CSV: {str(e)}")
        return False


if __name__ == "__main__":
    test_customer_csv()
