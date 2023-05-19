from book.api.serializers import *
from book.models import *
from rest_framework import generics
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
import django_filters
from django_filters import rest_framework
import datetime
from django.db.models import Sum, F, Case, When


@api_view(['POST'])
def ImportLogCreate(request):
    serialized = ImportLogForBM1Serializer(data=request.data, many=True)
    if serialized.is_valid():
        serialized.save()
        return Response(serialized.data, status=status.HTTP_201_CREATED)
    return Response(serialized._errors, status=status.HTTP_400_BAD_REQUEST)


class BookFilter(django_filters.FilterSet):
    Author = django_filters.CharFilter(method='filter_author')
    Category = django_filters.CharFilter(method='filter_category')

    def filter_author(self, queryset, name, value):
        authors = value.split(',')
        return queryset.filter(Author__in=authors)

    def filter_category(self, queryset, name, value):
        categories = value.split(',')
        return queryset.filter(Category__in=categories)

    class Meta:
        model = BOOK
        fields = ['Name', 'Category', 'Author']


class BookList(generics.ListAPIView):
    queryset = BOOK.objects.all()
    serializer_class = BookForBM3Serializer
    filter_backends = [rest_framework.DjangoFilterBackend]
    filterset_fields = ["Name", "Author", "Category"]
    filterset_class = BookFilter


class Setting(generics.ListCreateAPIView):
    queryset = CONSTRAINT.objects.all()
    serializer_class = ConstraintForSettingSerializer


@api_view(['GET'])
def BooksPerMonth(request):
    month = int(request.GET.get('month'))
    year = int(request.GET.get('year'))

    # Calculate the first day of the given month/year
    first_day_of_month = datetime.date(year, month, 1)

    # Retrieve the latest ImportLog before the first day of the given month for each book
    import_logs = IMPORTLOG.objects.filter(ImportDate__lt=first_day_of_month) \
        .order_by('Book', '-ImportDate') \
        .distinct('Book')

    # Calculate the sum of the positive imports for each book in the specified month
    import_sums = IMPORTLOG.objects.filter(ImportDate__year=year, ImportDate__month=month) \
        .values('Book') \
        .annotate(import_sum=Sum(F('Amount') * Case(When(Amount__gt=0, then=1), default=0))) \
        .filter(import_sum__gt=0)

    # Create a dictionary to store the import sums for each book
    import_sum_dict = {import_sum['Book']: import_sum['import_sum'] for import_sum in import_sums}

    books = []
    for import_log in import_logs:
        book = import_log.Book
        serializer = BookForQueryAmountSerializer(book)
        book_data = serializer.data

        book_data['result_by_month'] = {
            'FirstAmount': import_log.UpdatedAmount,
            'ImportCount': import_sum_dict.get(book.id, 0),  # Get the import sum for the book
            'LastAmount': import_log.UpdatedAmount + import_sum_dict.get(book.id, 0)
        }

        books.append(book_data)

    return Response(books, status=status.HTTP_200_OK)
