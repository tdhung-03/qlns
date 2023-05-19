from rest_framework import serializers
from customer.models import *
from book.models import *
from django.db import transaction


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = CUSTOMER
        fields = '__all__'


class CustomerForBM2Serializer(serializers.ModelSerializer):
    class Meta:
        model = CUSTOMER
        fields = ["FullName", "PhoneNumber"]


class BookForBM2Serializer(serializers.ModelSerializer):
    class Meta:
        model = BOOK
        fields = ["Name", "Category"]


class BillDetailForBM2Serializer(serializers.ModelSerializer):
    Book = BookForBM2Serializer()

    class Meta:
        model = BILLDETAIL
        fields = ["Book", "Amount", "SoldPrice"]


class BillForBM2Serializer(serializers.ModelSerializer):
    Customer = CustomerForBM2Serializer()
    BillDetails = BillDetailForBM2Serializer(many=True)

    @transaction.atomic
    def create(self, validated_data):
        customer_data = validated_data.pop("Customer")
        bill_details_data = validated_data.pop("BillDetails")
        billdate = validated_data.get("BillDate")
        constraint = CONSTRAINT.objects.last()
        try:
            customer = CUSTOMER.objects.get(PhoneNumber=customer_data["PhoneNumber"])
        except CUSTOMER.DoesNotExist:
            customer_serializer = CustomerForBM2Serializer(data=customer_data)
            if customer_serializer.is_valid():
                customer = customer_serializer.save()
            else:
                raise serializers.ValidationError(customer_serializer.errors)
        if customer.Debt > constraint.MaxDebt:
            raise serializers.ValidationError(f"This customer has debt bigger than {constraint.MaxDebt}")
        bill = BILL.objects.create(Customer=customer, **validated_data)
        for bill_detail_data in bill_details_data:
            book_data = bill_detail_data.pop("Book")
            amount_data = bill_detail_data.get("Amount")
            book_name = book_data.get("Name")
            try:
                book = BOOK.objects.get(Name=book_name)
            except BOOK.DoesNotExist:
                raise serializers.ValidationError(f"Book with name '{book_name}' does not exist.")
            if book.Amount - amount_data < constraint.BookAmountAfter:
                raise serializers.ValidationError(f"The quantity is very less")
            IMPORTLOG.objects.create(ImportDate=billdate, Book=book, Amount=-amount_data,
                                     PrevAmount=book.Amount, UpdatedAmount=book.Amount - amount_data)
            BILLDETAIL.objects.create(Bill=bill, Book=book, **bill_detail_data)
        for bill_detail in bill.BillDetails.all():
            book = bill_detail.Book
            book.Amount -= bill_detail.Amount
            book.save()
        customer.Debt = (customer.Debt or 0) + bill.Debt
        customer.save()
        return bill

    class Meta:
        model = BILL
        fields = ["Customer", "BillDate", "BillDetails", "TotalPrice", "Paid", "Debt"]


class CustomerForBM4Serializer(serializers.ModelSerializer):
    class Meta:
        model = CUSTOMER
        fields = ["FullName", "Address", "PhoneNumber", "Email"]


class DebtLogForBM4Serializer(serializers.ModelSerializer):
    Customer = CustomerForBM4Serializer()

    @transaction.atomic
    def create(self, validated_data):
        customer_data = validated_data.pop("Customer")
        constraint = CONSTRAINT.objects.last()
        try:
            customer = CUSTOMER.objects.get(PhoneNumber=customer_data["PhoneNumber"])
        except CUSTOMER.DoesNotExist:
            raise serializers.ValidationError(
                f"Customer with phone number '{customer_data['PhoneNumber']}' does not exist.")
        paid = validated_data["Paid"]
        if customer.Debt is None:
            customer.Debt = 0
        if customer.Debt - paid < 0 and constraint.PaidNotGreaterThanDebt:
            raise serializers.ValidationError(f"Paid is greater than customer's debt!")
        else:
            customer.Debt -= paid
            customer.save()
        if customer_data.get("Address"):
            customer.Address = customer_data["Address"]
        if customer_data.get("PhoneNumber"):
            customer.PhoneNumber = customer_data["PhoneNumber"]
        if customer_data.get("Email"):
            customer.Email = customer_data["Email"]
        customer.save()
        debt_log = DEBTLOG.objects.create(Customer=customer, **validated_data)
        debt_log.PrevDebt = customer.Debt + paid
        debt_log.UpdatedDebt = debt_log.PrevDebt - paid
        debt_log.save()
        return debt_log

    class Meta:
        model = DEBTLOG
        fields = ["Customer", "DebtDate", "Paid"]
