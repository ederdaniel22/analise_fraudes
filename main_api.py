"""Script para iniciar a API FastAPI do FraudShield."""
import uvicorn
from src.api import app

if __name__ == "__main__":
    print("""
    ╔════════════════════════════════════════════════════╗
    ║        FraudShield - API Server            ║
    ║                                                    ║
    ║  Acesse em: http://localhost:8000                 ║
    ║                                                    ║
    ║  Credenciais de Teste:                            ║
    ║  - Admin: admin@neobank.com / admin123            ║
    ║  - Analista: analista@neobank.com / analista123   ║
    ║  - Cliente: cliente@neobank.com / cliente123      ║
    ╚════════════════════════════════════════════════════╝
    """)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
