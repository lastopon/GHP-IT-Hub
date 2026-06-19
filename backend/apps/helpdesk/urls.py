"""Helpdesk module routes (mounted at /api/v1/helpdesk/)."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    KnowledgeBaseArticleViewSet,
    TicketCategoryViewSet,
    TicketCommentViewSet,
    TicketViewSet,
)

router = DefaultRouter()
router.register("categories", TicketCategoryViewSet, basename="ticketcategory")
router.register("tickets", TicketViewSet, basename="ticket")
router.register("comments", TicketCommentViewSet, basename="ticketcomment")
router.register("kb", KnowledgeBaseArticleViewSet, basename="kbarticle")

urlpatterns = [
    path("", include(router.urls)),
]
