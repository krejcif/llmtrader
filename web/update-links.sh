#!/bin/bash

# Add CSS link to all HTML files
for file in index.html logs.html strategy.html; do
    if [ -f "$file" ]; then
        # Check if link already exists
        if ! grep -q "dark-theme-final.css" "$file"; then
            # Add link before </head>
            sed -i 's|</head>|    <link rel="stylesheet" href="dark-theme-final.css">\n</head>|' "$file"
            echo "✅ Added CSS link to $file"
        else
            echo "ℹ️  CSS link already exists in $file"
        fi
    fi
done
