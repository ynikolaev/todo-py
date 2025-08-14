from rest_framework import serializers

from .models import Category, Task, TelegramAccount


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name"]


class TaskSerializer(serializers.ModelSerializer):
    categories = CategorySerializer(many=True, read_only=True)
    category_ids = serializers.PrimaryKeyRelatedField(
        many=True, write_only=True, queryset=Category.objects.all(), source="categories"
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
        ]

    def create(self, validated_data):
        categories = validated_data.pop("categories", [])
        task = Task.objects.create(user=self.context["request"].user, **validated_data)
        if categories:
            task.categories.set(categories)
        return task


class TelegramAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = TelegramAccount
        fields = ["id", "chat_id"]
