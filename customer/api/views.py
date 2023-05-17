from customer.api.serializers import *
from customer.models import *
from rest_framework import generics


class BillList(generics.ListCreateAPIView):
    queryset = BILL.objects.all()
    serializer_class = BillForBM2Serializer


class DebtLogList(generics.ListCreateAPIView):
    queryset = DEBTLOG.objects.all()
    serializer_class = DebtLogForBM4Serializer


class CustomerDetail(generics.RetrieveAPIView):
    queryset = CUSTOMER.objects.all()
    serializer_class = CustomerSerializer
    lookup_field = 'PhoneNumber'


class CustomerList(generics.ListAPIView):
    queryset = CUSTOMER.objects.all()
    serializer_class = CustomerSerializer
