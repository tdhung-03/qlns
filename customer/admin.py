from django.contrib import admin
from customer.models import CUSTOMER, BILL, DEBTLOG, BILLDETAIL

# Register your models here.
admin.site.register(CUSTOMER)
admin.site.register(BILL)
admin.site.register(DEBTLOG)
admin.site.register(BILLDETAIL)
