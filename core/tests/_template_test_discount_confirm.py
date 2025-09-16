from django.test import SimpleTestCase, RequestFactory
from django.http import JsonResponse

# Template no-DB test for discounts confirm gate
# Copy and adapt into real test file (remove leading underscore to run)

class TemplateDiscountConfirmGateTest(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def _call_post_on_view(self, view_callable):
        req = self.factory.post('/api/v1/rewards/discounts/confirm/')
        # minimal headers / auth can be added if needed
        return view_callable(req)

    def test_confirm_gate_off_returns_410(self):
        # Example usage: import the FBV and call via _call_post_on_view
        # from rewards.views.discount_views import confirm_discount
        # with override_settings(TEOCOIN_SYSTEM='database'):
        #     resp = self._call_post_on_view(confirm_discount)
        #     self.assertEqual(resp.status_code, 410)
        #     self.assertIn(b'feature_disabled', resp.content)
        pass
