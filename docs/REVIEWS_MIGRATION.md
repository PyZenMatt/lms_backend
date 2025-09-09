Migration for per-area review comments

This change introduces three new nullable text fields on `ExerciseReview`:

- `technical_comment`
- `creative_comment`
- `following_comment`

These are intended to be the canonical textual comments associated with the
three rating areas displayed in the frontend cards (Technique / Creative /
Following). Narrative fields (`strengths_comment`, `suggestions_comment`,
`final_comment`) remain in place for backward compatibility.

Developer steps to apply locally or on deployment:

```bash
# from lms_backend/ directory (project root)
python manage.py makemigrations courses   # optional if migration already created
python manage.py migrate
```

Notes:
- We intentionally do NOT attempt to split existing `comment` blobs into the
  new per-area fields automatically. That mapping is lossy and may introduce
  noise.
- Frontend should start sending `technical_comment`, `creative_comment` and
  `following_comment` when reviewers edit/save reviews. The backend will
  persist them once present.
