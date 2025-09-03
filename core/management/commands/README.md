# Setup Scripts

Questa cartella contiene script per il setup iniziale e la creazione di dati di test.

## Script di Creazione Dati
- `create_test_data.py` - Crea dati di test base
- `create_achievements.py` - Crea achievements e badge
- `create_approval_test_data.py` - Crea dati per test di approvazione

## Script di Test e Performance
- `test_performance.py` - Test delle performance del sistema
- `test_reward_system.py` - Test del sistema di ricompense
- `test_config.py` - Test delle configurazioni
- `final_test.py` - Test finale completo

## Script di Amministrazione
- `quick_admin_test.py` - Test rapido per admin

## Come utilizzare

```bash
# Setup dati di test base
python scripts/setup/create_test_data.py

# Creare achievements
python scripts/setup/create_achievements.py

# Test performance
python scripts/setup/test_performance.py

# Test completo finale
python scripts/setup/final_test.py
```

## Ordine raccomandato di esecuzione

1. `create_test_data.py` - Setup base
2. `create_achievements.py` - Aggiunge achievements
3. `create_approval_test_data.py` - Dati per approvazioni
4. `test_config.py` - Verifica configurazioni
5. `final_test.py` - Test completo

## Note
- Eseguire sempre in ambiente di sviluppo
- Alcuni script richiedono privilegi di admin
- Verificare che il database sia configurato correttamente
