#!/bin/bash
# Cleanup script for temporary and testing files

echo "🧹 Cleaning up temporary files..."

# 1. Remove Python cache files
echo "  Removing Python cache files..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete 2>/dev/null
find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null

# 2. Remove .DS_Store files (macOS)
echo "  Removing .DS_Store files..."
find . -name ".DS_Store" -delete 2>/dev/null

# 3. List migration-related files that can be archived
echo ""
echo "📦 Migration files (consider archiving these):"
echo "  scripts/create_migration_snapshot.py - Used for creating snapshots"
echo "  scripts/rollback_data_migration.py - Rollback script (keep for safety)"
echo "  scripts/generate_post_migration_report.py - Validation script (keep for future use)"
echo "  data/migration_snapshots/ - Pre-migration snapshots (archive after 30 days)"

# 4. Check for large log files
echo ""
echo "📊 Large files (>1MB):"
find . -type f -size +1M 2>/dev/null | grep -E '\.(log|json|csv)$' | while read file; do
    size=$(du -h "$file" | cut -f1)
    echo "  $size - $file"
done

echo ""
echo "✅ Cleanup complete!"
