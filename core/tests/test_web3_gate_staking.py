import json
from django.http import JsonResponse
from django.test import SimpleTestCase, RequestFactory, override_settings

from core.decorators.web3_gate import require_web3_enabled


def _payload(resp):
    return json.loads(resp.content.decode("utf-8")) if resp.content else {}


# A light-weight surrogate that represents a pass-through view when web3 is enabled.
def _pass_through(request):
    return JsonResponse({"ok": True})


class TestRequireWeb3Enabled_Staking(SimpleTestCase):
    def setUp(self):
        self.rf = RequestFactory()

    @override_settings(TEOCOIN_SYSTEM="database", USE_DB_TEOCOIN_SYSTEM=True)
    def test_stake_compat_gated_when_database_mode(self):
        # Wrap the surrogate with the decorator to exercise the gate logic
        gated = require_web3_enabled(_pass_through)
        req = self.rf.post("/api/v1/services/staking/stake/")
        resp = gated(req)
        assert resp.status_code == 410
        assert _payload(resp).get("code") == "feature_disabled"

    @override_settings(TEOCOIN_SYSTEM="blockchain", USE_DB_TEOCOIN_SYSTEM=False)
    def test_stake_compat_pass_through_when_blockchain_mode(self):
        gated = require_web3_enabled(_pass_through)
        req = self.rf.post("/api/v1/services/staking/stake/")
        resp = gated(req)
        assert resp.status_code == 200
        assert _payload(resp) == {"ok": True}

    def test_source_contains_decorator_annotation(self):
        # Ensure the compatibility view is annotated in source for review.
        import inspect
        import rewards.views.teocoin_views as tv

        src = inspect.getsource(tv)
        assert "@require_web3_enabled" in src
