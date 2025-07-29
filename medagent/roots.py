"""
URL patterns for the MedAgent app.

Routes API endpoints to their corresponding views. These endpoints include
OTP request and verification, chat session creation, messaging, ending
sessions, and retrieving summaries.
"""

from django.urls import path
from . import views

urlpatterns = [
    path("api/otp/request/", views.RequestOTP.as_view()),
    path("api/otp/verify/", views.VerifyOTP.as_view()),

    path("api/session/create/", views.CreateSession.as_view()),
    path("api/session/<int:session_id>/message/", views.PostMessage.as_view()),
    path("api/session/end/", views.EndSession.as_view()),

    path("api/patient/<int:patient_id>/summary/", views.GetPatientSummary.as_view()),
    path("api/session/<int:session_id>/summary/", views.GetSessionSummary.as_view()),
]
