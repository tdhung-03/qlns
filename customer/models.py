from django.db import models
from book.models import BOOK


# Create your models here.
class CUSTOMER(models.Model):
    FullName = models.TextField(max_length=100)
    Address = models.TextField(max_length=100, null=True, blank=True)
    PhoneNumber = models.TextField(max_length=100)
    Email = models.EmailField(null=True, blank=True)
    Debt = models.IntegerField(null=True, blank=True, default=0)

    def __str__(self):
        return self.PhoneNumber


class BILL(models.Model):
    BillDate = models.DateTimeField()
    Customer = models.ForeignKey(CUSTOMER, on_delete=models.PROTECT)
    TotalPrice = models.IntegerField()
    Paid = models.IntegerField()
    Debt = models.IntegerField()


class BILLDETAIL(models.Model):
    Book = models.ForeignKey(BOOK, on_delete=models.PROTECT)
    Bill = models.ForeignKey(BILL, on_delete=models.PROTECT, related_name="BillDetails")
    Amount = models.IntegerField()
    SoldPrice = models.IntegerField()


class DEBTLOG(models.Model):
    DebtDate = models.DateTimeField()
    Customer = models.ForeignKey(CUSTOMER, on_delete=models.PROTECT)
    PrevDebt = models.IntegerField(default=0)
    Paid = models.IntegerField()
    UpdatedDebt = models.IntegerField(default=0)
