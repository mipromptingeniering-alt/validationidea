#!/bin/bash

echo "📦 Instalando Git hooks..."

# Crear directorio hooks si no existe
mkdir -p .git/hooks

# Copiar pre-commit hook
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
bash scripts/pre-commit-tests.sh
EOF

# Hacer ejecutable
chmod +x .git/hooks/pre-commit
chmod +x scripts/pre-commit-tests.sh

echo "✅ Hooks instalados"
echo ""
echo "Ahora los tests se ejecutarán automáticamente antes de cada commit"
echo ""
