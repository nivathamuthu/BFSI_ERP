from django.urls import include, path
from rest_framework.routers import SimpleRouter

from finance.views import InvoiceViewSet, OutstandingBalanceView, TransactionViewSet

router = SimpleRouter()
router.register("transactions", TransactionViewSet, basename="transaction")
router.register("invoices", InvoiceViewSet, basename="invoice")

urlpatterns = [
    path(
        "customers/<int:customer_id>/outstanding-balance/",
        OutstandingBalanceView.as_view(),
        name="outstanding-balance",
    ),
    path("", include(router.urls)),
]
