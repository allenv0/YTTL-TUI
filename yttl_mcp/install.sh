#!/bin/bash

# YTTL MCP Server Installation Script

set -e

echo "🚀 Installing YTTL MCP Server..."

# Check Python version
python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "📋 Python version: $python_version"

if [[ $(echo "$python_version < 3.8" | bc -l) -eq 1 ]]; then
    echo "❌ Error: Python 3.8 or higher is required"
    exit 1
fi

# Install dependencies
echo "📦 Installing dependencies..."
pip3 install -r requirements.txt

# Install in development mode
echo "🔧 Installing YTTL MCP Server..."
pip3 install -e .

echo "✅ Installation complete!"
echo ""
echo "📋 Next steps:"
echo "1. Make sure your YTTL project has processed some videos (check ../out directory)"
echo "2. Configure Claude Desktop by adding this to ~/.claude_desktop_config.json:"
echo ""
echo '{'
echo '  "mcpServers": {'
echo '    "yttl": {'
echo '      "command": "python3",'
echo '      "args": ["-m", "yttl_mcp.server"],'
echo "      \"cwd\": \"$(pwd)\""
echo '    }'
echo '  }'
echo '}'
echo ""
echo "3. Restart Claude Desktop"
echo "4. Test with: python3 -m yttl_mcp.server"
echo ""
echo "🎉 Ready to use YTTL with Claude Desktop!"