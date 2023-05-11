from book.api.serializers import *
from book.models import *
from rest_framework import generics
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
import django_filters
from django_filters import rest_framework


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

# class BookAmountsList(generics.ListAPIView):
#     queryset = Book.objects.all()
#     serializer_class = BookWithAmountsSerializer
#
#     def get_serializer_context(self):
#         # Pass the month and year as context to the serializer
#         context = super().get_serializer_context()
#         context.update({
#             "month": self.request.query_params.get("month"),
#             "year": self.request.query_params.get("year")
#         })
#         return context
