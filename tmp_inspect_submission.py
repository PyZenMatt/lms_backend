import json
from django.core.serializers.json import DjangoJSONEncoder
from courses.models import ExerciseSubmission
s = ExerciseSubmission.objects.get(id=6)
out = []
qs = s.reviews.filter(reviewed_at__isnull=False)
for r in qs:
    out.append({
        'id': getattr(r, 'id', None),
        'reviewer': (r.reviewer.username if getattr(r, 'reviewer', None) else None),
        'technical_comment': getattr(r, 'technical_comment', None),
        'creative_comment': getattr(r, 'creative_comment', None),
        'following_comment': getattr(r, 'following_comment', None),
        'comment': getattr(r, 'comment', None),
        'reviewed_at': getattr(r, 'reviewed_at', None),
    })
print(json.dumps({'submission_id': getattr(s, 'id', None), 'reviews': out}, cls=DjangoJSONEncoder))
