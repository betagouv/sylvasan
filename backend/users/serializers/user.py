from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Prefetch

from organisations.models import Organisation, Pole
from organisations.serializers import MembershipSerializer
from organisations.serializers.organisation import FullOrganisationSerializer
from rest_framework import serializers
from surveys.serializers import VocabularySetDisplaySerializer
from surveys.views.vocabularyset import _accessible_vocab_queryset

from users.models import User


class UserRegistrationSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True, default="")
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    password_confirm = serializers.CharField(write_only=True)

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Cet identifiant est déjà utilisé.")
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Un compte avec cet email existe déjà.")
        return value

    def validate(self, data):
        if data["password"] != data["password_confirm"]:
            raise serializers.ValidationError({"password_confirm": "Les mots de passe ne correspondent pas."})
        try:
            validate_password(data["password"])
        except DjangoValidationError as e:
            raise serializers.ValidationError({"password": list(e.messages)})
        return data

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        password = validated_data.pop("password")
        return User.objects.create_user(
            email=validated_data.pop("email"),
            password=password,
            is_active=False,
            **validated_data,
        )


class UserDisplaySerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id",
            "first_name",
            "last_name",
        )


class UserExportSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id",
            "external_id",
            "email",
            "first_name",
            "last_name",
        )


class SimpleUserSerializer(serializers.ModelSerializer):
    memberships = MembershipSerializer(many=True, read_only=True)
    organisations = serializers.SerializerMethodField()
    vocabularies = serializers.SerializerMethodField()

    def get_organisations(self, obj):
        orgs = (
            Organisation.objects.filter(memberships__user=obj)
            .distinct()
            .prefetch_related(Prefetch("poles", queryset=Pole.objects.filter(is_active=True).order_by("name")))
        )
        return FullOrganisationSerializer(orgs, many=True).data

    def get_vocabularies(self, obj):
        return VocabularySetDisplaySerializer(_accessible_vocab_queryset(obj), many=True).data

    class Meta:
        model = User
        fields = (
            "id",
            "first_name",
            "last_name",
            "username",
            "memberships",
            "organisations",
            "vocabularies",
            "source",
        )
