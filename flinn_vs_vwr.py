import csv
import re
import os

# List of common color names
color_names = ['red', 'green', 'blue', 'yellow', 'orange', 'purple', 'pink', 'brown', 'black', 'white', 'gray', 'silver']

# Function to remove colors and ml/mm values from a string
def clean_text(text):
    # Remove colors
    for color in color_names:
        text = re.sub(rf'\b{color}\b', '', text, flags=re.IGNORECASE)
    # Remove ml and mm values
    text = re.sub(r'\b\d+(\.\d+)?\s*(mL|mm)\b', '', text, flags=re.IGNORECASE)
    # Remove standalone numbers
    text = re.sub(r'\b\d+\b', '', text)
    return text.strip()

# Function to get word sets from product names
def get_word_set(text):
    # Split the text into words, remove any empty words
    return set(word for word in re.split(r'\W+', text) if word)

# Function to get the word similarity ratio between two sets of words
def word_similarity(set1, set2):
    return len(set1 & set2) / len(set1 | set2)

def match_products(flinn_products, vwr_products, initial_threshold, threshold_decrement, output_folder):
    matched_products = []
    threshold = initial_threshold
    prev_threshold = None  # Initialize prev_threshold to None

    # Get the absolute path of the output folder
    output_folder_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), output_folder)

    # Create the output folder if it doesn't exist
    os.makedirs(output_folder_path, exist_ok=True)

    while threshold >= 0:
        print(f"Matching products with threshold: {threshold:.2f}")  # Round the threshold to 2 decimal places for printing
        output_file = os.path.join(output_folder_path, f"FlinnVsVWR_{threshold:.2f}.csv")  # Round the threshold to 2 decimal places for the file name

        if prev_threshold is None or threshold != prev_threshold:  # Check if the threshold has changed
            unmatched_flinn_products = []

            with open(output_file, 'w', newline='', encoding='utf-8') as master_file:
                writer = csv.writer(master_file)
                # Write headers
                writer.writerow(['Flinn_product_category', 'Flinn_product_sub_category', 'Flinn_product_id', 'Flinn_product_name', 'Flinn_product_quantity', 'Flinn_product_price', 'Flinn_product_url', 'VWR_product_category', 'VWR_product_sub_category', 'VWR_product_id', 'VWR_product_name', 'VWR_product_quantity', 'VWR_product_price', 'VWR_product_url', 'Match_Score'])

                # Loop through each Flinn product and find the best match from VWR's products
                for original_flinn_row, flinn_word_set in flinn_products:
                    original_flinn_product = original_flinn_row['Flinn_product_name']
                    best_match = None
                    best_match_score = 0

                    for original_vwr_row, vwr_word_set in vwr_products:
                        similarity = word_similarity(flinn_word_set, vwr_word_set)
                        if similarity > best_match_score:
                            best_match_score = similarity
                            best_match = original_vwr_row

                    # Find the colors in the original product names
                    flinn_colors = [color for color in color_names if re.search(rf'\b{color}\b', original_flinn_product, re.IGNORECASE)]
                    vwr_colors = [color for color in color_names if best_match and re.search(rf'\b{color}\b', best_match['VWR_product_name'], re.IGNORECASE)]

                    # Check ml/mm values in the original product names
                    flinn_ml_mm = re.findall(r'\b\d+(\.\d+)?\s*(mL|mm)\b', original_flinn_product, re.IGNORECASE)
                    vwr_ml_mm = re.findall(r'\b\d+(\.\d+)?\s*(mL|mm)\b', best_match['VWR_product_name'], re.IGNORECASE) if best_match else []

                    if best_match_score >= threshold:
                        if set(flinn_colors) == set(vwr_colors) and set(flinn_ml_mm) == set(vwr_ml_mm):
                            writer.writerow([original_flinn_row['Flinn_product_category'], original_flinn_row['Flinn_product_sub_category'], original_flinn_row['Flinn_product_id'], original_flinn_product, original_flinn_row['Flinn_product_quantity'], original_flinn_row['Flinn_product_price'], original_flinn_row['Flinn_product_url'], best_match['VWR_product_category'], best_match['VWR_product_sub_category'], best_match['VWR_product_id'], best_match['VWR_product_name'], best_match['VWR_product_quantity'], best_match['VWR_product_price'], best_match['VWR_product_url'], best_match_score])
                            print(f"{original_flinn_product} -> {best_match} (Match Score: {best_match_score}, Colors and mL/mm Match)")
                            matched_products.append((original_flinn_row, original_vwr_row, best_match_score))
                        elif set(flinn_colors) == set(vwr_colors):
                            writer.writerow([original_flinn_row['Flinn_product_category'], original_flinn_row['Flinn_product_sub_category'], original_flinn_row['Flinn_product_id'], original_flinn_product, original_flinn_row['Flinn_product_quantity'], original_flinn_row['Flinn_product_price'], original_flinn_row['Flinn_product_url'], best_match['VWR_product_category'], best_match['VWR_product_sub_category'], best_match['VWR_product_id'], best_match['VWR_product_name'], best_match['VWR_product_quantity'], best_match['VWR_product_price'], best_match['VWR_product_url'], best_match_score])
                            print(f"{original_flinn_product} -> {best_match} (Match Score: {best_match_score}, Colors Match, mL/mm Mismatch)")
                            matched_products.append((original_flinn_row, original_vwr_row, best_match_score))
                        else:
                            writer.writerow([original_flinn_row['Flinn_product_category'], original_flinn_row['Flinn_product_sub_category'], original_flinn_row['Flinn_product_id'], original_flinn_product, original_flinn_row['Flinn_product_quantity'], original_flinn_row['Flinn_product_price'], original_flinn_row['Flinn_product_url'], best_match['VWR_product_category'], best_match['VWR_product_sub_category'], best_match['VWR_product_id'], best_match['VWR_product_name'], best_match['VWR_product_quantity'], best_match['VWR_product_price'], best_match['VWR_product_url'], best_match_score])
                            print(f"{original_flinn_product} -> {best_match} (Match Score: {best_match_score}, Colors Mismatch)")
                            matched_products.append((original_flinn_row, original_vwr_row, best_match_score))
                    else:
                        writer.writerow([original_flinn_row['Flinn_product_category'], original_flinn_row['Flinn_product_sub_category'], original_flinn_row['Flinn_product_id'], original_flinn_product, original_flinn_row['Flinn_product_quantity'], original_flinn_row['Flinn_product_price'], original_flinn_row['Flinn_product_url'], '', '', '', 'No good match found (Low match score)', '', '', '', 0])
                        print(f"{original_flinn_product} -> No good match found (Low match score)")
                        unmatched_flinn_products.append((original_flinn_row, flinn_word_set))

            # Read the unmatched Flinn products from the current output file
            with open(output_file, 'r', encoding='utf-8') as master_file:
                reader = csv.DictReader(master_file)
                flinn_products = [(row, get_word_set(clean_text(row['Flinn_product_name']))) for row in reader if row['VWR_product_name'] == 'No good match found (Low match score)']

            # Get the unmatched VWR products for the next iteration
            with open('VWR_WARDS_Products.csv', 'r', encoding='utf-8') as vwr_file:
                vwr_reader = csv.DictReader(vwr_file)
                unmatched_vwr_products = []
                for vwr_row in vwr_reader:
                    vwr_product_name = vwr_row['VWR_product_name']
                    if vwr_row not in [match[1] for match in matched_products]:
                        unmatched_vwr_products.append((vwr_row, get_word_set(clean_text(vwr_product_name))))

            vwr_products = unmatched_vwr_products
            prev_threshold = threshold  # Store the current threshold
            threshold = round(threshold - threshold_decrement, 2)  # Round the new threshold to 2 decimal places

    return matched_products

# Open the two CSV files
with open('Flinn_Products.csv', 'r', encoding='utf-8') as flinn_file, open('VWR_WARDS_Products.csv', 'r', encoding='utf-8') as vwr_file:
    flinn_reader = csv.DictReader(flinn_file)
    vwr_reader = csv.DictReader(vwr_file)

    # Read the product names and store original and modified names
    flinn_products = [(row, get_word_set(clean_text(row['Flinn_product_name']))) for row in flinn_reader]
    vwr_products = [(row, get_word_set(clean_text(row['VWR_product_name']))) for row in vwr_reader]

# Set the initial threshold, threshold decrement, and output folder
initial_threshold = 0.8
threshold_decrement = 0.01
output_folder = 'FlinnVsVWR'

# Match the products with decreasing thresholds
matched_products = match_products(flinn_products, vwr_products, initial_threshold, threshold_decrement, output_folder)

# Collect matched products into a separate CSV file
final_output_file = os.path.join(output_folder, 'Matched_Products.csv')
with open(final_output_file, 'w', newline='', encoding='utf-8') as final_file:
    writer = csv.writer(final_file)
    writer.writerow(['Flinn_product_category', 'Flinn_product_sub_category', 'Flinn_product_id', 'Flinn_product_name', 'Flinn_product_quantity', 'Flinn_product_price', 'Flinn_product_url', 'VWR_product_category', 'VWR_product_sub_category', 'VWR_product_id', 'VWR_product_name', 'VWR_product_quantity', 'VWR_product_price', 'VWR_product_url', 'Match_Score'])
    for match in matched_products:
        writer.writerow([match[0]['Flinn_product_category'], match[0]['Flinn_product_sub_category'], match[0]['Flinn_product_id'], match[0]['Flinn_product_name'], match[0]['Flinn_product_quantity'], match[0]['Flinn_product_price'], match[0]['Flinn_product_url'], match[1]['VWR_product_category'], match[1]['VWR_product_sub_category'], match[1]['VWR_product_id'], match[1]['VWR_product_name'], match[1]['VWR_product_quantity'], match[1]['VWR_product_price'], match[1]['VWR_product_url'], match[2]])

print(f"Final matched products have been saved to {final_output_file}")
