"""
URL configuration for Gymnassic project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
"""

from django.contrib import admin
from django.urls import path

urlpatterns = [
    path("admin/", admin.site.urls),
]

# Customize admin site headers
admin.site.site_header = "Gymnassic Admin"
admin.site.site_title = "Gymnassic Admin Portal"
admin.site.index_title = "Welcome to Gymnassic Management System"

