"""Auth + user/department API views."""
from django.contrib.auth import get_user_model
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import AuditLog, Department
from .permissions import IsAdmin, ReadOnlyOrAdmin
from .serializers import (
    CustomTokenObtainPairSerializer,
    DepartmentSerializer,
    MeSerializer,
    UserCreateSerializer,
    UserSerializer,
)

User = get_user_model()


def _client_ip(request):
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


class LoginView(TokenObtainPairView):
    """POST email+password -> {access, refresh, user}. Logs the attempt."""

    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        email = request.data.get("email", "")
        try:
            # SimpleJWT raises AuthenticationFailed on bad credentials, so a
            # failed login never reaches the post-call code below — we must
            # audit it in the except branch and re-raise.
            response = super().post(request, *args, **kwargs)
        except Exception:
            AuditLog.objects.create(
                action=AuditLog.Action.LOGIN_FAILED,
                target=f"user:{email}",
                ip_address=_client_ip(request),
            )
            raise

        actor = User.objects.filter(email=email).first()
        AuditLog.objects.create(
            actor=actor,
            action=AuditLog.Action.LOGIN,
            target=f"user:{email}",
            ip_address=_client_ip(request),
        )
        return response


class UserViewSet(viewsets.ModelViewSet):
    """CRUD for users. Admin-managed; everyone can read their own via /me."""

    queryset = User.objects.all().order_by("email")
    permission_classes = [IsAdmin]
    filterset_fields = ["role", "department", "is_active"]
    search_fields = ["email", "first_name", "last_name", "employee_id"]
    ordering_fields = ["email", "date_joined", "role"]

    def get_serializer_class(self):
        if self.action == "create":
            return UserCreateSerializer
        return UserSerializer

    @action(
        detail=False,
        methods=["get", "patch"],
        permission_classes=[IsAuthenticated],
    )
    def me(self, request):
        """Read or update the currently authenticated user's own profile."""
        if request.method == "PATCH":
            # Users may edit a limited set of their own fields.
            allowed = {"first_name", "last_name", "phone"}
            data = {k: v for k, v in request.data.items() if k in allowed}
            serializer = UserSerializer(request.user, data=data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
        return Response(MeSerializer(request.user).data)


class DepartmentViewSet(viewsets.ModelViewSet):
    """CRUD for departments. Read for all authenticated, write for admin."""

    queryset = Department.objects.filter(is_active=True).order_by("name")
    serializer_class = DepartmentSerializer
    permission_classes = [ReadOnlyOrAdmin]
    search_fields = ["name", "code"]
