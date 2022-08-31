from django.urls import path
from . import views

urlpatterns = [
    path('search/', views.DocSearch.as_view(), name='doc_search'),
    path('', views.DocListView.as_view(), name='docs')
]
