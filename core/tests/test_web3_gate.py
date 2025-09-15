import json
from django.http import JsonResponse
from django.test import SimpleTestCase, RequestFactory, override_settings
from django.utils.decorators import method_decorator
from django.views import View

from lms_backend.core.decorators.web3_gate import require_web3_enabled


def _payload(resp):
    return json.loads(resp.content.decode("utf-8")) if resp.content else {}

# ----- Function-based view -----
def fbv_ok(request):
    return JsonResponse({"ok": True})

fbv_gated = require_web3_enabled(fbv_ok)


class TestRequireWeb3Enabled_FBV(SimpleTestCase):
    def setUp(self):
        self.rf = RequestFactory()

    @override_settings(TEOCOIN_SYSTEM="database", USE_DB_TEOCOIN_SYSTEM=True)
    def test_gated_when_database_mode(self):
        req = self.rf.post("/x")
        resp = fbv_gated(req)
        assert resp.status_code == 410
        assert _payload(resp).get("code") == "feature_disabled"
        assert _payload(resp).get("reason") == "web3_disabled"

    @override_settings(TEOCOIN_SYSTEM="blockchain", USE_DB_TEOCOIN_SYSTEM=False)
    def test_pass_through_when_blockchain_mode(self):
        req = self.rf.post("/x")
        resp = fbv_gated(req)
        assert resp.status_code == 200
        assert _payload(resp) == {"ok": True}


# ----- Class-based view (CBV) -----
class DummyPostView(View):
    @method_decorator(require_web3_enabled)
    def post(self, request, *args, **kwargs):
        return JsonResponse({"ok": True})


class TestRequireWeb3Enabled_CBV(SimpleTestCase):
    def setUp(self):
        self.rf = RequestFactory()
        self.view = DummyPostView.as_view()

    @override_settings(TEOCOIN_SYSTEM="database", USE_DB_TEOCOIN_SYSTEM=True)
    def test_cbv_gated_when_database_mode(self):
        req = self.rf.post("/cbv")
        resp = self.view(req)
        assert resp.status_code == 410
        assert _payload(resp).get("code") == "feature_disabled"

    @override_settings(TEOCOIN_SYSTEM="blockchain", USE_DB_TEOCOIN_SYSTEM=False)
    def test_cbv_pass_through_when_blockchain_mode(self):
        req = self.rf.post("/cbv")
        resp = self.view(req)
        assert resp.status_code == 200
        assert _payload(resp) == {"ok": True}
