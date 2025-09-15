from django.test import SimpleTestCase, RequestFactory, override_settings
from django.http import JsonResponse


class DiscountConfirmGateTest(SimpleTestCase):
    """No-DB checks for the web3 gate.

    - Validate the `require_web3_enabled` decorator returns 410 when off and
      does not return 410 when on by applying it to a small dummy view.
    - Confirm the `rewards/views/discount_views.py` file contains the
      `@require_web3_enabled` annotation for `confirm_discount` (evidence).
    """

    def setUp(self):
        self.factory = RequestFactory()

    def _dummy_view(self, request):
        return JsonResponse({"ok": True}, status=200)

    def test_decorator_returns_410_when_off(self):
        from core.decorators.web3_gate import require_web3_enabled

        wrapped = require_web3_enabled(self._dummy_view)
        req = self.factory.post('/api/v1/rewards/discounts/confirm/')

        with override_settings(TEOCOIN_SYSTEM='database'):
            resp = wrapped(req)
            self.assertEqual(resp.status_code, 410)
            self.assertIn(b'feature_disabled', resp.content)

    def test_decorator_not_410_when_on(self):
        from core.decorators.web3_gate import require_web3_enabled

        wrapped = require_web3_enabled(self._dummy_view)
        req = self.factory.post('/api/v1/rewards/discounts/confirm/')

        with override_settings(TEOCOIN_SYSTEM='blockchain', USE_DB_TEOCOIN_SYSTEM=False):
            resp = wrapped(req)
            self.assertNotEqual(resp.status_code, 410)

    def test_confirm_view_is_decorated(self):
        # Evidence: confirm_discount should be annotated in source with the gate
        fn = 'lms_backend/rewards/views/discount_views.py'
        src = open(fn, 'r', encoding='utf-8').read()
        self.assertIn('@require_web3_enabled', src)
