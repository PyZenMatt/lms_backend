"""
URL patterns for TeoCoin Discount System API

Provides REST endpoints for the gas-free discount system
"""

from django.urls import path
from .discount_views import (
    SignatureDataView,
    CreateDiscountRequestView, 
    ApproveDiscountRequestView,
    DeclineDiscountRequestView,
    DiscountRequestDetailView,
    StudentRequestsView,
    TeacherRequestsView,
    DiscountStatsView,
    CalculateDiscountCostView,
    SystemStatusView
)
# Import Layer 2 views - COMMENTED OUT - Missing file
# from .layer2_discount_views import (
#     create_layer2_discount_request,
#     check_student_teo_balance,
#     simulate_layer2_discount
# )

app_name = 'discount_api'

urlpatterns = [
    # === Layer 2 Gas-Free Endpoints (NEW) === COMMENTED OUT - Missing views
    # path('layer2/create/', create_layer2_discount_request, name='layer2_create_request'),
    # path('layer2/balance/', check_student_teo_balance, name='layer2_check_balance'),
    # path('layer2/simulate/', simulate_layer2_discount, name='layer2_simulate'),
    
    # === Original Smart Contract Endpoints (LEGACY) ===
    # Signature and request creation
    path('signature-data/', SignatureDataView.as_view(), name='signature_data'),
    path('create/', CreateDiscountRequestView.as_view(), name='create_request'),
    
    # Request management
    path('approve/', ApproveDiscountRequestView.as_view(), name='approve_request'),
    path('decline/', DeclineDiscountRequestView.as_view(), name='decline_request'),
    
    # Request details and listings
    path('request/<int:request_id>/', DiscountRequestDetailView.as_view(), name='request_detail'),
    path('student/<str:student_address>/', StudentRequestsView.as_view(), name='student_requests'),
    path('teacher/<str:teacher_address>/', TeacherRequestsView.as_view(), name='teacher_requests'),
    
    # Utilities and stats
    path('calculate/', CalculateDiscountCostView.as_view(), name='calculate_cost'),
    path('stats/', DiscountStatsView.as_view(), name='stats'),
    path('status/', SystemStatusView.as_view(), name='system_status'),
]
