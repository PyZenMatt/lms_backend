# 🎁 MVP Reward Logic for Exercise Completion

## ✅ Obiettivo

Implementare un sistema di ricompensa base per gli studenti che superano un esercizio, con limite massimo proporzionato al prezzo del corso.

---

## 🎯 Regole principali

1. Ogni esercizio completato (con successo) può generare una ricompensa **randomica tra lo 0% e il 5% del costo totale del corso**.
2. La somma totale delle ricompense generate da tutti gli esercizi del corso **non può superare il 15% del prezzo del corso**.
3. Il reward massimo è distribuito **casualmente** tra gli esercizi promossi.
4. Se la ricompensa residua disponibile per il corso è minore del reward calcolato, si limita l’importo all'importo residuo.

---

## ⚙️ Esempio pratico

- Corso: "Disegno Creativo" — prezzo = 100 TeoCoin
- Lezione superata da uno studente → reward calcolata tra 0% e 5% → tra 0 e 5 TeoCoin
- Tutte le lezioni insieme possono generare **massimo 15 TeoCoin** di reward per quel corso

---

## 🧠 Strategia tecnica

### 1. Nuovo campo in `Course` (models.py)
```python
reward_distributed = models.PositiveIntegerField(default=0)
```

### 2. Nuovo campo in `ExerciseSubmission`
```python
reward_amount = models.PositiveIntegerField(default=0)
```

### 3. Logica lato backend (es. in ReviewExerciseView)
```python
reward_max = int(course.price * 0.15)
reward_remaining = reward_max - course.reward_distributed

if reward_remaining > 0:
    random_reward = random.randint(1, min(int(course.price * 0.05), reward_remaining))
    course.reward_distributed += random_reward
    submission.reward_amount = random_reward
    submission.student.add_teo_coins(random_reward)
    submission.save()
    course.save()
```

---

## 📌 Considerazioni

- La reward viene data **solo se l’esercizio è promosso**
- Questo sistema è sicuro: non si superano mai i limiti economici
- In futuro si potrà estendere la logica con:
  - Bonus per performance
  - Loot casuali
  - Badge o premi settimanali

---

## 🚀 Pronto per MVP

Con questa logica puoi:
- Attivare un sistema di reward controllato
- Incentivare l'apprendimento
- Aggiungere TeoCoin agli studenti in modo meritocratico e scalabile

> "Studia, esercitati, supera... e guadagna TeoCoin!"

---

Sezione pronta per essere collegata alle tue `views` e `models`! ✅
