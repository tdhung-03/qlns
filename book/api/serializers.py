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
        invalid_books = []
        try:
            book = BOOK.objects.get(Name=book_data["Name"])
            if book.Amount > constraint.AmountNeedImport:
                invalid_books.append(book.Name)
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

        if len(invalid_books) > 0:
            raise serializers.ValidationError(
                f"The following books have amount larger than {constraint.AmountNeedImport}: {', '.join(invalid_books)}")

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


class BookForQueryAmountSerializer(serializers.ModelSerializer):
    class Meta:
        model = BOOK
        fields = ["Name"]
