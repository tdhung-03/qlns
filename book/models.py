from django.db import models


# Create your models here.
class BOOK(models.Model):
    Name = models.TextField(max_length=100)
    Category = models.TextField(max_length=100)
    Author = models.TextField(max_length=100)
    ImportPrice = models.IntegerField()
    Amount = models.IntegerField()

    def __str__(self):
        return self.Name


class IMPORTLOG(models.Model):
    ImportDate = models.DateTimeField()
    Book = models.ForeignKey(BOOK, on_delete=models.PROTECT)
    PrevAmount = models.IntegerField(default=0)
    Amount = models.IntegerField()
    UpdatedAmount = models.IntegerField(default=0)
    TotalPrice = models.IntegerField()


class CONSTRAINT(models.Model):
    MinImport = models.IntegerField(default=150)
    AmountNeedImport = models.IntegerField(default=300)
    MaxDebt = models.IntegerField(default=1000000)
    BookAmountAfter = models.IntegerField(default=20)
    PaidNotGreaterThanDebt = models.BooleanField(default=True)
