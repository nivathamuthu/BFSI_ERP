from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from core.constants import UserRole
from core.models import User


def tokens_for(user):
    refresh = RefreshToken.for_user(user)
    refresh["role"] = user.role
    access = refresh.access_token
    return {
        "refresh": str(refresh),
        "access": str(access),
        "role": user.role,
        "username": user.get_username(),
    }


class ApiModuleSerializer(serializers.Serializer):
    name = serializers.CharField()
    path = serializers.CharField()
    purpose = serializers.CharField()


class ApiRootSerializer(serializers.Serializer):
    name = serializers.CharField()
    summary = serializers.CharField()
    docs = serializers.CharField()
    schema = serializers.CharField()
    modules = ApiModuleSerializer(many=True)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "role"]
        read_only_fields = ["id", "username", "email"]

    def validate_role(self, value):
        if (
            self.instance
            and self.instance.role == UserRole.ADMIN
            and value != UserRole.ADMIN
            and not User.objects.filter(role=UserRole.ADMIN).exclude(pk=self.instance.pk).exists()
        ):
            raise serializers.ValidationError("Cannot remove the last admin.")
        return value


class AuthResponseSerializer(serializers.Serializer):
    refresh = serializers.CharField()
    access = serializers.CharField()
    role = serializers.CharField()
    username = serializers.CharField()
    user = UserSerializer()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ["username", "email", "password", "role"]
        extra_kwargs = {"role": {"required": False}}

    def validate(self, attrs):
        if attrs.get("role") == UserRole.ADMIN and User.objects.exists():
            raise serializers.ValidationError({"role": "Admin role cannot be self-assigned."})
        candidate = User(username=attrs.get("username", ""), email=attrs.get("email", ""))
        try:
            validate_password(attrs["password"], user=candidate)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"password": list(exc.messages)}) from exc
        return attrs

    def create(self, validated_data):
        password = validated_data.pop("password")
        role = validated_data.pop("role", UserRole.CLAIMS_ADJUSTER)
        first_account = not User.objects.exists()
        if first_account:
            role = UserRole.ADMIN
        user = User(role=role, **validated_data)
        if first_account:
            user.is_superuser = True
            user.is_staff = True
        user.set_password(password)
        user.save()
        return user


class AppTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["role"] = user.role
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data["role"] = self.user.role
        data["username"] = self.user.get_username()
        return data
