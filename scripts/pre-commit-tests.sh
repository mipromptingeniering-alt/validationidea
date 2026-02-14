#!/bin/bash

echo ""
echo "============================================================"
echo "🧪 EJECUTANDO PRE-COMMIT TESTS"
echo "============================================================"
echo ""

# Test workflow
python tests/test_workflow.py

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Tests fallaron - commit bloqueado"
    echo ""
    exit 1
fi

echo ""
echo "✅ Tests pasados - continuando commit"
echo ""

exit 0
