#!/bin/bash

# Output file
OUTPUT_FILE="SPA_Context.md"

# Clear existing file
echo "# WealthOS SPA Codebase Context" > "$OUTPUT_FILE"
echo "Generated on $(date)" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

# Function to append file content
append_file() {
    local file_path=$1
    if [ -f "$file_path" ]; then
        echo "## File: $file_path" >> "$OUTPUT_FILE"
        echo '```'${file_path##*.} >> "$OUTPUT_FILE"
        cat "$file_path" >> "$OUTPUT_FILE"
        echo '```' >> "$OUTPUT_FILE"
        echo "" >> "$OUTPUT_FILE"
        echo "Added $file_path"
    else
        echo "Warning: File $file_path not found"
    fi
}

echo "Packing configuration files..."
append_file "package.json"
append_file "vite.config.ts"
append_file "tsconfig.json"
append_file "index.html"

echo "Packing source code..."
# Find all TS, TSX, CSS files in src
find src -name "*.tsx" -o -name "*.ts" -o -name "*.css" | sort | while read -r file; do
    append_file "$file"
done

echo "Done! Context saved to $OUTPUT_FILE"
echo "You can now upload $OUTPUT_FILE to Google AI Studio."
