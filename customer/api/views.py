from customer.api.serializers import *
from customer.models import *
from rest_framework import generics
from rest_framework.decorators import api_view
import datetime
from django.db.models import Sum, F, Case, When, Min
from rest_framework.response import Response
from rest_framework import status


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


@api_view(['GET'])
def CustomersPerMonth(request):
    month = int(request.GET.get('month'))
    year = int(request.GET.get('year'))

    # Calculate the first day of the given month/year
    first_day_of_month = datetime.date(year, month, 1)

    # Retrieve the latest DebtLog before the first day of the given month for each customer
    debt_logs_before_month = DEBTLOG.objects.filter(DebtDate__lt=first_day_of_month) \
        .order_by('Customer', '-DebtDate') \
        .distinct('Customer')

    # Retrieve the first DebtLog within the given month for each customer
    debt_logs_within_month = DEBTLOG.objects.filter(DebtDate__year=year, DebtDate__month=month) \
        .exclude(DebtDate__lt=first_day_of_month) \
        .order_by('Customer', 'DebtDate') \
        .distinct('Customer')

    # Combine the debt logs from before the month and within the month
    debt_logs = debt_logs_before_month | debt_logs_within_month

    # Calculate the sum of the negative debts for each customer in the specified month
    debt_sums = DEBTLOG.objects.filter(DebtDate__year=year, DebtDate__month=month) \
        .values('Customer') \
        .annotate(debt_sum=Sum(F('Paid') * Case(When(Paid__lt=0, then=1), default=0))) \
        .filter(debt_sum__lt=0)

    # Create a dictionary to store the debt sums for each customer
    debt_sum_dict = {debt_sum['Customer']: debt_sum['debt_sum'] for debt_sum in debt_sums}

    customers = []
    for debt_log in debt_logs:
        customer = debt_log.Customer
        serializer = CustomerForQueryDebtSerializer(customer)
        customer_data = serializer.data

        # Check if the debt log is the first log within the given month
        first_log_within_month = DEBTLOG.objects.filter(Customer=customer, DebtDate__year=year, DebtDate__month=month) \
            .aggregate(first_debt=Min('DebtDate'))

        if first_log_within_month['first_debt'] == debt_log.DebtDate:
            # Set FirstDebt to 0 for the first debt log within the given month
            customer_data['result_by_month'] = {
                'FirstDebt': 0,
                'DebtSum': -debt_sum_dict.get(customer.id, 0),
                'LastDebt': -debt_sum_dict.get(customer.id, 0),
            }
        else:
            # Retrieve the latest debt log before the given month for the customer
            latest_log_before_month = DEBTLOG.objects.filter(Customer=customer, DebtDate__lt=first_day_of_month) \
                .order_by('-DebtDate') \
                .first()

            if latest_log_before_month:
                # Calculate the FirstDebt using the latest debt log before the given month
                customer_data['result_by_month'] = {
                    'FirstDebt': latest_log_before_month.UpdatedDebt,
                    'DebtSum': -debt_sum_dict.get(customer.id, 0),
                    'LastDebt': latest_log_before_month.UpdatedDebt - debt_sum_dict.get(customer.id, 0)
                }
            else:
                # If there are no debt logs before the given month, set FirstDebt to 0
                customer_data['result_by_month'] = {
                    'FirstDebt': 0,
                    'DebtSum': -debt_sum_dict.get(customer.id, 0),
                    'LastDebt': -debt_sum_dict.get(customer.id, 0),
                }

        customers.append(customer_data)

    return Response(customers, status=status.HTTP_200_OK)
