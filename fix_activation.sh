#!/bin/bash
# Quick fix script for virtual environment activation issues

echo "🔧 Fixing virtual environment activation..."

# Create the proper activation script
cat > /home/ubuntu/activate-migration << 'EOF'
#!/bin/bash
# This script should be sourced, not executed
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo "⚠️  This script should be sourced, not executed directly."
    echo "💡 Run: source activate-migration"
    exit 1
fi

cd /home/ubuntu/Migration
source venv/bin/activate
echo "✅ Virtual environment activated!"
echo "📍 Current directory: $(pwd)"
echo "🐍 Python: $(which python)"
EOF

chmod +x /home/ubuntu/activate-migration

# Update the start-migration.sh script
cat > /home/ubuntu/start-migration.sh << 'EOF'
#!/bin/bash
cd /home/ubuntu/Migration
echo "🚀 Migration environment ready!"
echo "Available scripts:"
echo "  • DB_compare.py - Compare Redis databases"
echo "  • ReadWriteOps.py - Performance testing"
echo "  • flushDBData.py - Database cleanup"
echo "  • manage_env.py - Environment configuration"
echo "  • DataFaker.py - Generate test data"
echo "  • provision_elasticache.py - Create ElastiCache instances"
echo "  • cleanup_elasticache.py - Remove ElastiCache resources"
echo ""
echo "💡 To activate the virtual environment, run:"
echo "   source activate-migration"
echo ""
echo "🔄 Or manually:"
echo "   cd /home/ubuntu/Migration && source venv/bin/activate"
EOF

chmod +x /home/ubuntu/start-migration.sh

# Create a migration command for new shell
cat > /home/ubuntu/migration << 'EOF'
#!/bin/bash
cd /home/ubuntu/Migration
source venv/bin/activate
exec bash --rcfile <(echo "PS1='(migration) \u@\h:\w\$ '")
EOF

chmod +x /home/ubuntu/migration

# Update .bashrc with proper alias and PATH
if ! grep -q "activate-migration" /home/ubuntu/.bashrc; then
    echo 'export PATH="/home/ubuntu:$PATH"' >> /home/ubuntu/.bashrc
    echo 'alias activate-migration="source /home/ubuntu/activate-migration"' >> /home/ubuntu/.bashrc
fi

echo "✅ Fix applied successfully!"
echo ""
echo "🎯 Now you can use:"
echo "   source activate-migration    # Activate venv in current shell"
echo "   migration                    # Start new shell with venv activated"
echo "   ./start-migration.sh         # Show available scripts and instructions"
echo ""
echo "💡 You may need to run 'source ~/.bashrc' or start a new SSH session for the alias to work"
