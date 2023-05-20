from django.urls import path
from customer.api.views import *

urlpatterns = [
    path("bills/", BillList.as_view()),
    path("debt-logs/", DebtLogList.as_view()),
    path("customers/", CustomerList.as_view()),
    path("customers/<str:PhoneNumber>/", CustomerDetail.as_view()),
    path("customers-per-month/", CustomersPerMonth)
]
