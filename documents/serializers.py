from pathlib import Path

from django.conf import settings
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from documents.models import Document

ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".doc", ".docx"}
LINK_FOR_TYPE = {
    Document.DocType.POLICY: "policy",
    Document.DocType.CLAIM: "claim",
    Document.DocType.UNDERWRITING: "underwriting_request",
}


class DocumentSerializer(serializers.ModelSerializer):
    file = serializers.FileField(write_only=True, required=False)
    url = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = [
            "id",
            "name",
            "type",
            "size",
            "content_type",
            "url",
            "file",
            "policy",
            "claim",
            "underwriting_request",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "size", "content_type", "url", "created_at", "updated_at"]
        extra_kwargs = {"name": {"required": False}}

    @extend_schema_field(serializers.CharField())
    def get_url(self, obj) -> str:
        if not obj.file:
            return ""
        url = obj.file.url
        request = self.context.get("request")
        if request is not None:
            return request.build_absolute_uri(url)
        return url

    def _value(self, attrs, field):
        if field in attrs:
            return attrs[field]
        if self.instance is not None:
            return getattr(self.instance, field)
        return None

    def validate(self, attrs):
        uploaded = attrs.get("file")
        if self.instance is None and uploaded is None:
            raise serializers.ValidationError({"file": "A file is required."})
        if uploaded is not None:
            extension = Path(uploaded.name).suffix.lower()
            if extension not in ALLOWED_EXTENSIONS:
                raise serializers.ValidationError(
                    {"file": "Unsupported file type. Upload a PDF, Word document, or image."}
                )
            if uploaded.size > settings.MAX_UPLOAD_BYTES:
                limit_mb = settings.MAX_UPLOAD_BYTES / (1024 * 1024)
                raise serializers.ValidationError(
                    {"file": f"File exceeds the {limit_mb:g} MB upload limit."}
                )
            if not attrs.get("name") and self._value(attrs, "name") in (None, ""):
                attrs["name"] = Path(uploaded.name).name

        if self.instance is None and not attrs.get("name"):
            raise serializers.ValidationError({"name": "A document name is required."})

        doc_type = self._value(attrs, "type")
        required = LINK_FOR_TYPE.get(doc_type)
        if required and self._value(attrs, required) is None:
            raise serializers.ValidationError({required: "This document type must be linked to a record."})

        claim = self._value(attrs, "claim")
        policy = self._value(attrs, "policy")
        if claim is not None and policy is not None and claim.policy_id != policy.id:
            raise serializers.ValidationError({"claim": "Claim does not belong to the selected policy."})
        return attrs

    def _apply_file(self, validated_data):
        uploaded = validated_data.get("file")
        if uploaded is None:
            return validated_data
        validated_data["size"] = uploaded.size
        validated_data["content_type"] = getattr(uploaded, "content_type", "") or ""
        return validated_data

    def create(self, validated_data):
        return super().create(self._apply_file(validated_data))

    def update(self, instance, validated_data):
        return super().update(instance, self._apply_file(validated_data))
