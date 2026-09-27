from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework_simplejwt.views import TokenObtainPairView

from core.models import User
from core.permissions import IsAdmin
from core.serializers import (
    ApiRootSerializer,
    AppTokenObtainPairSerializer,
    AuthResponseSerializer,
    RegisterSerializer,
    UserSerializer,
    tokens_for,
)


@extend_schema(responses=ApiRootSerializer)
class ApiRootView(APIView):
    """Map of the insurance operations this API covers."""

    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        return Response(
            {
                "name": "BFSI Insurance ERP",
                "summary": (
                    "Internal staff API for an insurer. A customer is underwritten, "
                    "a policy is bound, premiums are invoiced, and claims are adjusted "
                    "against active cover."
                ),
                "docs": request.build_absolute_uri("/api/docs/"),
                "schema": request.build_absolute_uri("/api/schema/"),
                "modules": [
                    {
                        "name": "Auth",
                        "path": "/api/auth/",
                        "purpose": "Register, log in, and assign admin, underwriter, or claims-adjuster",
                    },
                    {
                        "name": "Customers",
                        "path": "/api/customers/",
                        "purpose": "Policyholders and billing contacts",
                    },
                    {
                        "name": "Underwriting",
                        "path": "/api/underwriting/",
                        "purpose": "Risk decision before a policy can be bound",
                    },
                    {
                        "name": "Policies",
                        "path": "/api/policies/",
                        "purpose": "Coverage records. Claims require an active policy",
                    },
                    {
                        "name": "Claims",
                        "path": "/api/claims/",
                        "purpose": "Loss notices, status workflow, and rules-based fraud flags",
                    },
                    {
                        "name": "Finance",
                        "path": "/api/finance/",
                        "purpose": "Invoices, cash transactions, and outstanding balance",
                    },
                    {
                        "name": "Compliance",
                        "path": "/api/compliance/",
                        "purpose": "Control rules and the reports filed against them",
                    },
                    {
                        "name": "Documents",
                        "path": "/api/documents/",
                        "purpose": "Files attached to policies, claims, or underwriting",
                    },
                    {
                        "name": "Identity",
                        "path": "/api/identity/verify/",
                        "purpose": "Mock KYC check standing in for a provider such as Onfido",
                    },
                ],
            }
        )


@extend_schema(request=RegisterSerializer, responses={201: AuthResponseSerializer})
class RegisterView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        payload = tokens_for(user)
        payload["user"] = UserSerializer(user).data
        return Response(payload, status=status.HTTP_201_CREATED)


class AppTokenObtainPairView(TokenObtainPairView):
    serializer_class = AppTokenObtainPairSerializer


@extend_schema(responses=UserSerializer)
class MeView(APIView):
    def get(self, request):
        return Response(UserSerializer(request.user).data)


class UserViewSet(ModelViewSet):
    """Admin-only staff directory. Role changes are how desks are granted."""

    queryset = User.objects.all().order_by("id")
    serializer_class = UserSerializer
    permission_classes = [IsAdmin]
    http_method_names = ["get", "patch", "head", "options"]
