"""
URL configuration for bot project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from myapp.views import *

urlpatterns = [
    path('admin/', admin.site.urls),
    # path('', list_tables, name='list_tables'),
    # path('data/<str:table_name>/', get_table_data, name='table_data'),
    # path('api/<str:table_name>/', get_table_data_json, name='table_data_json'),
    # path('search/<str:table_name>/', search_table, name='search_table'),
    
    # NEW: Assessment processing routes
    path('process/pending/', process_pending_assessments, name='process_pending'),
    path('process/latest/', process_latest_assessment, name='process_latest'),
    path('process/<str:assessment_id>/', process_assessment_by_id, name='process_by_id'),


]
