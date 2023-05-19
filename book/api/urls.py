from django.urls import path
from book.api.views import *

urlpatterns = [
    path("books/", BookList.as_view()),
    path("import-logs-create/", ImportLogCreate),
    path("settings/", Setting.as_view()),
]
