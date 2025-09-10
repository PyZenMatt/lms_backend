from django.db import migrations


def backfill_per_area_comments(apps, schema_editor):
    ExerciseReview = apps.get_model('courses', 'ExerciseReview')
    # conservative heuristics: look for explicit labeled sections in the blob
    import re

    tech_rx = re.compile(r"(?:Technical|Technique)[\s:\-]+([\s\S]*?)(?:\n\s*Creative|\n\s*Following|$)", re.IGNORECASE)
    crea_rx = re.compile(r"Creative[\s:\-]+([\s\S]*?)(?:\n\s*Following|\n\s*Technical|$)", re.IGNORECASE)
    foll_rx = re.compile(r"Following[\s:\-]+([\s\S]*?)(?:\n\s*Technical|\n\s*Creative|$)", re.IGNORECASE)

    to_save = []
    for r in ExerciseReview.objects.all():
        blob = (getattr(r, 'comment', None) or '')
        if not blob:
            continue
        # Only backfill empty per-area fields
        tc = getattr(r, 'technical_comment', None)
        cc = getattr(r, 'creative_comment', None)
        fc = getattr(r, 'following_comment', None)
        changed = False
        if not tc:
            m = tech_rx.search(blob)
            if m:
                txt = m.group(1).strip()
                if txt:
                    r.technical_comment = txt
                    changed = True
        if not cc:
            m = crea_rx.search(blob)
            if m:
                txt = m.group(1).strip()
                if txt:
                    r.creative_comment = txt
                    changed = True
        if not fc:
            m = foll_rx.search(blob)
            if m:
                txt = m.group(1).strip()
                if txt:
                    r.following_comment = txt
                    changed = True
        if changed:
            to_save.append(r)

    if to_save:
        for obj in to_save:
            obj.save(update_fields=[f for f in ('technical_comment','creative_comment','following_comment') if getattr(obj, f, None)])


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0011_add_per_area_comments'),
    ]

    operations = [
        migrations.RunPython(backfill_per_area_comments, reverse_code=migrations.RunPython.noop),
    ]
