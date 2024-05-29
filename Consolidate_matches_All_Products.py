import csv
import os

def consolidate_matches(input_folder, output_file, supplier_name):
    matched_products = []

    input_folder_path = os.path.abspath(input_folder)
    csv_files = [f for f in os.listdir(input_folder_path) if f.endswith('.csv') and f.startswith(f'FlinnVs{supplier_name}')]

    for csv_file in csv_files:
        file_path = os.path.join(input_folder_path, csv_file)
        with open(file_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row[f'{supplier_name}_product_name'] != 'No good match found (Low match score)':
                    match_score = float(row['Match_Score'])
                    if match_score < 0.3:
                        for key in [f'{supplier_name}_product_category', f'{supplier_name}_product_sub_category', f'{supplier_name}_product_id', f'{supplier_name}_product_name', f'{supplier_name}_product_quantity', f'{supplier_name}_product_price', f'{supplier_name}_product_url']:
                            row[key] = ''
                    matched_products.append(row)

    with open(output_file, 'w', newline='') as final_file:
        fieldnames = ['Flinn_product_category', 'Flinn_product_sub_category', 'Flinn_product_id', 'Flinn_product_name', 'Flinn_product_quantity', 'Flinn_product_price', 'Flinn_product_url', f'{supplier_name}_product_category', f'{supplier_name}_product_sub_category', f'{supplier_name}_product_id', f'{supplier_name}_product_name', f'{supplier_name}_product_quantity', f'{supplier_name}_product_price', f'{supplier_name}_product_url', 'Match_Score']
        writer = csv.DictWriter(final_file, fieldnames=fieldnames)
        writer.writeheader()
        for match in matched_products:
            writer.writerow(match)

    print(f"Final matched products have been saved to {output_file}")

def create_master_csv(suppliers, output_folder, output_file_name):
    master_products = {}

    # Ensure the output folder exists
    os.makedirs(output_folder, exist_ok=True)
    output_file = os.path.join(output_folder, output_file_name)

    for supplier_name in suppliers:
        input_file = f'FlinnVs{supplier_name}/Matched_Products.csv'
        with open(input_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                flinn_product_id = row['Flinn_product_id']
                if flinn_product_id not in master_products:
                    master_products[flinn_product_id] = {
                        'Flinn_product_category': row['Flinn_product_category'],
                        'Flinn_product_sub_category': row['Flinn_product_sub_category'],
                        'Flinn_product_id': row['Flinn_product_ids'],
                        'Flinn_product_name': row['Flinn_product_names'],
                        'Flinn_product_quantity': row['Flinn_product_quantities'],
                        'Flinn_product_price': row['Flinn_product_prices'],
                        'Flinn_product_url': row['Flinn_product_urls']
                    }
                master_products[flinn_product_id].update({
                    f'{supplier_name}_product_category': row[f'{supplier_name}_product_category'],
                    f'{supplier_name}_product_sub_category': row[f'{supplier_name}_product_sub_category'],
                    f'{supplier_name}_product_id': row[f'{supplier_name}_product_id'],
                    f'{supplier_name}_product_name': row[f'{supplier_name}_product_name'],
                    f'{supplier_name}_product_quantity': row[f'{supplier_name}_product_quantity'],
                    f'{supplier_name}_product_price': row[f'{supplier_name}_product_price'],
                    f'{supplier_name}_product_url': row[f'{supplier_name}_product_url'],
                    f'{supplier_name}_match_score': row['Match_Score']
                })

    with open(output_file, 'w', newline='') as final_file:
        fieldnames = ['Flinn_product_category', 'Flinn_product_sub_category', 'Flinn_product_id', 'Flinn_product_name', 'Flinn_product_quantity', 'Flinn_product_price', 'Flinn_product_url']
        for supplier_name in suppliers:
            fieldnames.extend([
                f'{supplier_name}_product_category', f'{supplier_name}_product_sub_category', f'{supplier_name}_product_id', f'{supplier_name}_product_name', f'{supplier_name}_product_quantity', f'{supplier_name}_product_price', f'{supplier_name}_product_url', f'{supplier_name}_match_score'
            ])
        writer = csv.DictWriter(final_file, fieldnames=fieldnames)
        writer.writeheader()
        for product in master_products.values():
            writer.writerow(product)

    print(f"Master CSV has been saved to {output_file}")

# Consolidate matches for each supplier
consolidate_matches('FlinnVsFrey', 'FlinnVsFrey/Matched_Products.csv', 'Frey')
consolidate_matches('FlinnVsNasco', 'FlinnVsNasco/Matched_Products.csv', 'Nasco')
consolidate_matches('FlinnVsVWR', 'FlinnVsVWR/Matched_Products.csv', 'VWR')
consolidate_matches('FlinnVsFisher', 'FlinnVsFisher/Matched_Products.csv', 'Fisher')


# Create the master CSV in a separate folder
suppliers = ['Frey', 'Nasco', 'VWR', 'Fisher']
create_master_csv(suppliers, 'MasterCSVFolder', 'Master_Matched_Products.csv')
