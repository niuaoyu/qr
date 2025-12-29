import json
import os

# Define paths
json_file_path = r"c:\Users\nay\Desktop\qr\qr\worldquant\arrange_combine\alpha_generator_config.json"
txt_file_path = r"C:\Users\nay\Desktop\qr\qr\worldquant\data_fields_txt\TOP3000\TOP3000_analyst4.txt"

def update_json_from_txt():
    # Check if text file exists
    if not os.path.exists(txt_file_path):
        print(f"Error: Text file not found at {txt_file_path}")
        return

    # Read fields from text file
    try:
        fields = []
        with open(txt_file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                # Split by whitespace to get columns, take the first one (id)
                parts = line.split()
                if parts:
                    field_id = parts[0]
                    # Skip the header row 'id'
                    if field_id.lower() != 'id':
                        fields.append(field_id)
        
        print(f"Read {len(fields)} fields from text file.")

        # Read JSON file
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Update the Fundamental list
        if 'template_params' not in data:
            data['template_params'] = {}
        
        data['template_params']['Fundamental'] = fields

        # Write back to JSON file
        with open(json_file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
        
        print(f"Successfully updated 'Fundamental' list in {json_file_path}")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    update_json_from_txt()
