from django.db import IntegrityError, transaction
from rest_framework import serializers

from .models import Category, Task, TelegramAccount


class TelegramAccountSerializer(serializers.ModelSerializer):
    # need to access fields in input
    user_id = serializers.IntegerField(required=True)
    chat_id = serializers.IntegerField(required=True)

    class Meta:
        model = TelegramAccount
        fields = ["user_id", "chat_id", "tg_username"]

    def validate(self, attrs):
        print("DEBUG TG ATTRS:", attrs, flush=True)
        return attrs


class CategorySerializer(serializers.ModelSerializer):
    tg = TelegramAccountSerializer(required=False, allow_null=True)

    class Meta:
        model = Category
        fields = ["id", "name", "tg"]

    def validate(self, attrs):
        print("DEBUG:", attrs, flush=True)
        return super().validate(attrs)

    def create(self, validated_data):
        tg_data = validated_data.pop("tg", None)
        user_id = tg_data.get("user_id")
        if not user_id:
            raise serializers.ValidationError(
                {"tg": {"user_id": f"This field is required. Got {validated_data}"}}
            )
        tg_instance = None

        with transaction.atomic():
            if tg_data:
                try:
                    user_id = int(tg_data.get("user_id"))
                    chat_id = int(tg_data.get("chat_id"))
                except (TypeError, ValueError) as err:
                    raise serializers.ValidationError(
                        {"tg": "user_id and chat_id must be integers"}
                    ) from err

                tg_username = tg_data.get("tg_username")
                tg_instance = TelegramAccount.objects.filter(
                    user_id=user_id, chat_id=chat_id
                ).first()
                if tg_instance:
                    TelegramAccount.update_if_different(tg_instance, tg_data)
                else:
                    tg_instance = TelegramAccount.objects.create(
                        user_id=user_id,
                        chat_id=chat_id,
                        tg_username=tg_username,
                    )
            try:
                with transaction.atomic():
                    return Category.objects.create(tg=tg_instance, **validated_data)
            except IntegrityError as err:
                raise serializers.ValidationError(
                    f"Category '{validated_data['name']}' already exists for this Telegram account."
                ) from err


class TaskSerializer(serializers.ModelSerializer):
    tg = TelegramAccountSerializer(required=False, allow_null=True)
    categories = CategorySerializer(many=True, read_only=True)
    category_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        write_only=True,
        queryset=Category.objects.all(),
        source="categories",  # maps to Task.categories m2m
    )

    class Meta:
        model = Task
        fields = [
            "id",
            "title",
            "description",
            "created_at",
            "due_at",
            "is_done",
            "categories",
            "category_ids",
            "tg",  # nested TelegramAccount data
        ]
        read_only_fields = ["id", "created_at", "categories"]

    def create(self, validated_data):
        categories = validated_data.pop("categories", [])
        tg_data = validated_data.pop("tg", None)

        # Find or create the TelegramAccount for this user
        tg_account, _ = TelegramAccount.objects.get_or_create(
            user_id=tg_data["user_id"],
            defaults={
                "chat_id": tg_data["chat_id"],
                "tg_username": tg_data.get("tg_username"),
            },
        )

        # If account exists but fields differ, update them
        TelegramAccount.update_if_different(tg_account, tg_data)

        task = Task.objects.create(tg=tg_account, **validated_data)
        if categories:
            task.categories.set(categories)

        return task

    def update(self, instance, validated_data):
        categories = validated_data.pop("categories", None)
        tg_data = validated_data.pop("tg", None)

        if tg_data:
            tg_account, _ = TelegramAccount.objects.get_or_create(
                user_id=tg_data["user_id"],
                defaults={
                    "chat_id": tg_data["chat_id"],
                    "tg_username": tg_data.get("tg_username"),
                },
            )
            TelegramAccount.update_if_different(tg_account, tg_data)
            instance.tg = tg_account

        if categories is not None:
            instance.categories.set(categories)

        return super().update(instance, validated_data)
