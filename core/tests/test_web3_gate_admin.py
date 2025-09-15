import json
from types import SimpleNamespace

from django.test import SimpleTestCase, RequestFactory, override_settings
from django.http import JsonResponse


class TestWeb3GateAdmin(SimpleTestCase):
    def setUp(self):
        self.rf = RequestFactory()

    # -------- ProcessPendingWithdrawalsView --------
    @override_settings(TEOCOIN_SYSTEM="database", USE_DB_TEOCOIN_SYSTEM=True)
    def test_process_pending_blocked_when_database(self):
        from lms_backend.api.withdrawal_views import ProcessPendingWithdrawalsView
        from lms_backend.core.decorators.web3_gate import require_web3_enabled

        # decorate the class method directly and call on instance (bypasses DRF dispatch/permissions)
        inst = ProcessPendingWithdrawalsView()
        req = self.rf.post("/fake")
        req.user = SimpleNamespace(id=1, email="a@x", is_authenticated=True)
        from rest_framework.request import Request as DRFRequest
        drf_req = DRFRequest(req)
        # ensure DRF Request exposes the test user
        drf_req._request.user = req.user
        decorated = require_web3_enabled(inst.post)
        resp = decorated(drf_req)
        assert resp.status_code == 410
        payload = json.loads(resp.content.decode("utf-8")) if resp.content else {}
        assert payload.get("code") == "feature_disabled"

    @override_settings(TEOCOIN_SYSTEM="blockchain", USE_DB_TEOCOIN_SYSTEM=False)
    def test_process_pending_passes_when_blockchain(self):
        # Avoid invoking heavy view logic; verify decorator passes-through when enabled
        from lms_backend.core.decorators.web3_gate import require_web3_enabled

        @require_web3_enabled
        def surrogate_ok(request):
            return JsonResponse({"ok": True}, status=200)

        req = self.rf.post("/fake")
        resp = surrogate_ok(req)
        assert resp.status_code == 200

    # -------- MintToAddressView --------
    @override_settings(TEOCOIN_SYSTEM="database", USE_DB_TEOCOIN_SYSTEM=True)
    def test_mint_to_address_blocked_when_database(self):
        from lms_backend.api.withdrawal_views import MintToAddressView
        from lms_backend.core.decorators.web3_gate import require_web3_enabled

        inst = MintToAddressView()
        # send JSON to avoid multipart form content-type
        req = self.rf.post(
            "/fake",
            data=json.dumps({"amount": "1", "to_address": "0x0"}),
            content_type="application/json",
        )
        req.user = SimpleNamespace(id=1, email="a@x", is_authenticated=True)
        from rest_framework.request import Request as DRFRequest
        drf_req = DRFRequest(req)
        drf_req._request.user = req.user
        decorated = require_web3_enabled(inst.post)
        resp = decorated(drf_req)
        assert resp.status_code == 410
        payload = json.loads(resp.content.decode("utf-8")) if resp.content else {}
        assert payload.get("code") == "feature_disabled"

    @override_settings(TEOCOIN_SYSTEM="blockchain", USE_DB_TEOCOIN_SYSTEM=False)
    def test_mint_to_address_passes_when_blockchain(self):
        # Avoid invoking heavy view logic; verify decorator passes-through when enabled
        from lms_backend.core.decorators.web3_gate import require_web3_enabled

        @require_web3_enabled
        def surrogate_ok(request):
            return JsonResponse({"ok": True}, status=201)

        req = self.rf.post("/fake")
        resp = surrogate_ok(req)
        assert resp.status_code in (200, 201)

    # -------- confirm_discount (FBV) --------
    @override_settings(TEOCOIN_SYSTEM="database", USE_DB_TEOCOIN_SYSTEM=True)
    def test_confirm_discount_blocked_when_database(self):
        # Avoid importing heavy module; confirm decorator is present in source and behaves correctly.
        import pathlib
        from lms_backend.core.decorators.web3_gate import require_web3_enabled

        src = pathlib.Path("lms_backend/rewards/views/discount_views.py").read_text()
        assert "@require_web3_enabled" in src

        @require_web3_enabled
        def surrogate(request):
            return JsonResponse({"ok": True})

        req = self.rf.post("/fake")
        resp = surrogate(req)
        assert resp.status_code == 410
        payload = json.loads(resp.content.decode("utf-8")) if resp.content else {}
        assert payload.get("code") == "feature_disabled"

    @override_settings(TEOCOIN_SYSTEM="blockchain", USE_DB_TEOCOIN_SYSTEM=False)
    def test_confirm_discount_passes_when_blockchain(self):
        from lms_backend.core.decorators.web3_gate import require_web3_enabled

        @require_web3_enabled
        def surrogate_ok(request):
            return JsonResponse({"ok": True})

        req = self.rf.post("/fake")
        resp = surrogate_ok(req)
        assert resp.status_code in (200, 201)

