from rest_framework import serializers
from book.models import *
from django.db import transaction


class BookForBM1Serializer(serializers.ModelSerializer):
    class Meta:
        model = BOOK
        fields = ["Name", "Category", "Author", "ImportPrice"]


class ImportLogForBM1Serializer(serializers.ModelSerializer):
    Book = BookForBM1Serializer()

    @transaction.atomic
    def create(self, validated_data):
        amount_data = validated_data.pop("Amount")
        constraint = CONSTRAINT.objects.last()
        if amount_data < constraint.MinImport:
            raise serializers.ValidationError(
                f"Import amount have to be greater than {constraint.MinImport}, check again!")
        book_data = validated_data.pop("Book")
        try:
            book = BOOK.objects.get(Name=book_data["Name"])
            if book.Amount > constraint.AmountNeedImport:
                raise serializers.ValidationError(
                    f"Just import book that has amount smaller than {constraint.AmountNeedImport}, check again!")
            for key, value in book_data.items():
                setattr(book, key, value)
            book.Amount += amount_data
            book.save()
        except BOOK.DoesNotExist:
            book_serializer = BookForBM1Serializer(data=book_data)
            if book_serializer.is_valid():
                book = book_serializer.save(Amount=amount_data)
            else:
                raise serializers.ValidationError(book_serializer.errors)
        import_log = IMPORTLOG.objects.create(Book=book, Amount=amount_data, **validated_data)
        import_log.PrevAmount = book.Amount - amount_data
        import_log.UpdatedAmount = import_log.PrevAmount + amount_data
        import_log.save()
        return import_log

    class Meta:
        model = IMPORTLOG
        fields = ["ImportDate", "Book", "Amount", "TotalPrice"]


class BookForBM3Serializer(serializers.ModelSerializer):
    class Meta:
        model = BOOK
        fields = ["Name", "Category", "Author", "Amount"]


class ConstraintForSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = CONSTRAINT
        fields = "__all__"

# class BookWithAmountsSerializer(serializers.ModelSerializer):
#     prev_amount = serializers.SerializerMethodField()
#     updated_amount = serializers.SerializerMethodField()
#
#     class Meta:
#         model = Book
#         fields = ["name", "prev_amount", "updated_amount"]
#
#     def get_prev_amount(self, obj):
#         # Get the previous amount of the book at the first day of the current month
#         import_logs = obj.importlog_set.filter(
#             import_date_time__month=self.context["month"],
#             import_date_time__year=self.context["year"]
#         ).order_by("import_date_time")
#
#         if import_logs.exists():
#             return import_logs.first().prev_amount
#
#         # Get the latest import log from the previous month and use its updated_amount as the prev_amount and updated_amount
#         last_month_logs = obj.importlog_set.filter(
#             import_date_time__month=int(self.context["month"]) - 1,
#             import_date_time__year=self.context["year"]
#         ).order_by("-import_date_time")
#
#         if last_month_logs.exists():
#             return last_month_logs.first().updated_amount
#
#         # If there are no import logs for the book, return its amount
#         return obj.amount
#
#     def get_updated_amount(self, obj):
#         # Get the updated amount of the book at the end of the current month
#         import_logs = obj.importlog_set.filter(
#             import_date_time__month=self.context["month"],
#             import_date_time__year=self.context["year"]
#         ).annotate(day=ExtractDay("import_date_time")).order_by("-day")
#
#         if import_logs.exists():
#             return import_logs.first().updated_amount
#
#         # Get the latest import log from the previous month and use its updated_amount as the updated_amount
#         last_month_logs = obj.importlog_set.filter(
#             import_date_time__month=int(self.context["month"]) - 1,
#             import_date_time__year=self.context["year"]
#         ).order_by("-import_date_time")
#
#         if last_month_logs.exists():
#             return last_month_logs.first().updated_amount
#
#         # If there are no import logs for the book, return its amount
#         return obj.amount
