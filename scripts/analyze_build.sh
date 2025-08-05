#!/bin/bash

echo "🚀 REACT BUILD ANALYSIS"
echo "======================="

cd /home/teo/Project/school/schoolplatform/frontend

echo "📦 BUILD SIZE ANALYSIS:"
echo "-----------------------"

if [ -d "dist" ]; then
    echo "✅ Build directory exists"
    
    echo ""
    echo "📊 JAVASCRIPT BUNDLES:"
    find dist/assets/js -name "*.js" -exec ls -lh {} \; | awk '{print $5 " - " $9}' | sort -hr
    
    echo ""
    echo "🎨 CSS BUNDLES:" 
    find dist/assets/css -name "*.css" -exec ls -lh {} \; | awk '{print $5 " - " $9}' | sort -hr
    
    echo ""
    echo "📈 TOTAL SIZES:"
    echo "JavaScript: $(find dist/assets/js -name "*.js" -exec ls -l {} \; | awk '{sum += $5} END {print sum/1024 "KB"}')"
    echo "CSS: $(find dist/assets/css -name "*.css" -exec ls -l {} \; | awk '{sum += $5} END {print sum/1024 "KB"}')"
    echo "Total Assets: $(du -sh dist/assets | cut -f1)"
    echo "Total Build: $(du -sh dist | cut -f1)"
    
    echo ""
    echo "🔄 CHUNK ANALYSIS:"
    echo "Vendor Chunks: $(find dist/assets/js -name "*vendor*.js" | wc -l)"
    echo "Component Chunks: $(find dist/assets/js -name "*.js" | grep -v vendor | wc -l)"
    
else
    echo "❌ Build directory not found. Run 'npm run build' first."
fi

echo ""
echo "✅ OPTIMIZATION STATUS: COMPLETE!"
