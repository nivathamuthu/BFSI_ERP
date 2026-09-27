import re

from rest_framework import serializers

from customers.models import Customer

PHONE_RE = re.compile(r"^\+?[0-9][0-9\-\s]{6,18}$")


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ["id", "name", "email", "phone", "address", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_phone(self, value):
        if value and not PHONE_RE.fullmatch(value):
            raise serializers.ValidationError("Enter a phone number with digits, spaces, or dashes.")
        return value
