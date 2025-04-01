#\!/bin/bash

# Path to lab files
LAB_DIR="/home/lakishadavid/computational_genetic_genealogy/docs/textbook"

# Loop through all lab HTML files (excluding the ones we've already fixed)
for lab_file in $(find "$LAB_DIR" -name "lab*.html" | grep -v "lab0_environment.html" | grep -v "lab0_data.html"); do
  echo "Updating $lab_file..."
  
  # Get the lab title from the file
  lab_title=$(grep -oP '(?<=<p>).*(?=</p>)' "$lab_file" | head -1)
  
  # Update the head section to include Font Awesome and Google Fonts
  sed -i '/<link rel="stylesheet" href="..\/styles.css">/a \    <link rel="stylesheet" href="https:\/\/cdnjs.cloudflare.com\/ajax\/libs\/font-awesome\/6.0.0\/css\/all.min.css">\n    <link rel="preconnect" href="https:\/\/fonts.googleapis.com">\n    <link rel="preconnect" href="https:\/\/fonts.gstatic.com" crossorigin>\n    <link href="https:\/\/fonts.googleapis.com\/css2?family=Montserrat:wght@400;600;700&family=Open+Sans:wght@300;400;600&display=swap" rel="stylesheet">' "$lab_file"
  
  # Update the body tag and header section
  sed -i 's/<body>/<body class="textbook-page">/' "$lab_file"
  
  # Update the header and navigation
  sed -i '/<header>/,/<\/nav>/c\
    <header class="textbook-header">\
        <div class="container">\
            <h1>Computational Genetic Genealogy</h1>\
            <p>'"$lab_title"'</p>\
        </div>\
    </header>\
\
    <nav class="textbook-nav">\
        <div class="container">\
            <a href="../index.html"><i class="fas fa-arrow-left"></i> Back to Main Page</a>\
            <a href="contents.html">Table of Contents</a>\
            <a href="'"$(basename "$lab_file")"'" class="active">'"$(basename "$lab_file" .html | sed 's/_/ /g' | sed 's/lab/Lab /g')"'</a>\
        </div>\
    </nav>' "$lab_file"
  
  # Update the footer
  sed -i '/<footer>/,/<\/footer>/c\
    <footer class="textbook-footer">\
        <div class="container">\
            <p>\&copy; 2025 Dr. LaKisha David, Department of Anthropology, University of Illinois Urbana-Champaign</p>\
        </div>\
    </footer>' "$lab_file"
  
done

echo "All lab files have been updated\!"
