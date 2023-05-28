from book.api.serializers import *
from book.models import *
from rest_framework import generics
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
import django_filters
from django_filters import rest_framework
import datetime
from django.db.models import Sum, F, Case, When, Min


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
    import_logs_before_month = IMPORTLOG.objects.filter(ImportDate__lt=first_day_of_month) \
        .order_by('Book', '-ImportDate') \
        .distinct('Book')

    # Retrieve the first ImportLog within the given month for each book
    import_logs_within_month = IMPORTLOG.objects.filter(ImportDate__year=year, ImportDate__month=month) \
        .exclude(ImportDate__lt=first_day_of_month) \
        .order_by('Book', 'ImportDate') \
        .distinct('Book')

    # Combine the import logs from before the month and within the month
    import_logs = import_logs_before_month | import_logs_within_month

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

        # Check if the import log is the first log within the given month
        first_log_within_month = IMPORTLOG.objects.filter(Book=book, ImportDate__year=year, ImportDate__month=month) \
            .aggregate(first_import=Min('ImportDate'))

        if first_log_within_month['first_import'] == import_log.ImportDate:
            # Set FirstAmount to 0 for the first import log within the given month
            book_data['result_by_month'] = {
                'FirstAmount': 0,
                'ImportCount': import_sum_dict.get(book.id, 0),
                'LastAmount': import_sum_dict.get(book.id, 0)
            }
        else:
            # Retrieve the latest import log before the given month for the book
            latest_log_before_month = IMPORTLOG.objects.filter(Book=book, ImportDate__lt=first_day_of_month) \
                .order_by('-ImportDate') \
                .first()

            if latest_log_before_month:
                # Calculate the FirstAmount using the latest import log before the given month
                book_data['result_by_month'] = {
                    'FirstAmount': latest_log_before_month.UpdatedAmount,
                    'ImportCount': import_sum_dict.get(book.id, 0),
                    'LastAmount': latest_log_before_month.UpdatedAmount + import_sum_dict.get(book.id, 0)
                }
            else:
                # If there are no import logs before the given month, set FirstAmount to 0
                book_data['result_by_month'] = {
                    'FirstAmount': 0,
                    'ImportCount': import_sum_dict.get(book.id, 0),
                    'LastAmount': import_sum_dict.get(book.id, 0)
                }

        books.append(book_data)

    return Response(books, status=status.HTTP_200_OK)
