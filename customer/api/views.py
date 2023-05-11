from customer.api.serializers import *
from customer.models import *
from rest_framework import generics


class BillList(generics.ListCreateAPIView):
    queryset = BILL.objects.all()
    serializer_class = BillForBM2Serializer


class DebtLogList(generics.ListCreateAPIView):
    queryset = DEBTLOG.objects.all()
    serializer_class = DebtLogForBM4Serializer
