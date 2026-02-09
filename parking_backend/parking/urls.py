from django.urls import path
# Views file-la irunthu ellathayum import pannikonga
from .views import (
    create_reservation,
    create_monthly_pass,
    create_yearly_pass,
    cancel_reservation, 
    create_employee,
    mark_as_scanned,      # Itha add panniten
    check_scan_status,     # Ithayum add panniten
    verify_face
)

urlpatterns = [
    path("reserve/", create_reservation, name="reserve"),
    path("create_monthly_pass/", create_monthly_pass, name="monthly-pass"),
    path("yearly-pass/", create_yearly_pass, name="yearly-pass"),
    path("cancel-reservation/", cancel_reservation, name="cancel-reservation"),
    path("new-employee/", create_employee, name='create_employee'),
    path("verify-face/", verify_face, name='verify_face'),
    
    # Prefix-a remove panniyachu, ഏன்னா main file-laye 'api/' irukku
    path('mark_as_scanned/<str:spot_id>/', mark_as_scanned, name='mark_as_scanned'),
    path('check_scan_status/<str:spot_id>/', check_scan_status, name='check_scan_status'),
]