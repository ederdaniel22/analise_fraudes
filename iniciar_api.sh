#!/bin/bash
# Script para iniciar o servidor da API FraudShield no Linux/Mac

clear

echo ""
echo "╔════════════════════════════════════════════════════╗"
echo "║        FraudShield - API Server            ║"
echo "║                                                    ║"
echo "║  Iniciando servidor...                            ║"
echo "║                                                    ║"
echo "║  Acesse em: http://localhost:8000                 ║"
echo "║                                                    ║"
echo "║  Credenciais de Teste:                            ║"
echo "║  - Admin: admin@neobank.com / admin123            ║"
echo "║  - Analista: analista@neobank.com / analista123   ║"
echo "║  - Cliente: cliente@neobank.com / cliente123      ║"
echo "║                                                    ║"
echo "║  Pressione Ctrl+C para parar o servidor           ║"
echo "╚════════════════════════════════════════════════════╝"
echo ""

python main_api.py
