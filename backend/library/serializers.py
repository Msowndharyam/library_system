from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from .models import User, Book, Borrow

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)
    email = serializers.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'role']

    def validate_password(self, value):
        validate_password(value)
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already exists")
        return value

    def validate_username(self, value):
        if len(value) < 3:
            raise serializers.ValidationError("Username must be at least 3 characters")
        return value

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            role=validated_data.get('role', 'user')
        )
        return user

class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = '__all__'
        read_only_fields = ['created_at']

    def validate_title(self, value):
        if not value.strip():
            raise serializers.ValidationError("Title cannot be empty")
        
        if self.instance is None:
            if Book.objects.filter(
                title__iexact=value.strip(),
                author__iexact=self.initial_data.get('author', '').strip()
            ).exists():
                raise serializers.ValidationError("Book with this title and author already exists")
        return value.strip()

    def validate_author(self, value):
        if not value.strip():
            raise serializers.ValidationError("Author cannot be empty")
        return value.strip()

    def validate_genre(self, value):
        if not value.strip():
            raise serializers.ValidationError("Genre cannot be empty")
        return value.strip()

class BorrowSerializer(serializers.ModelSerializer):
    book_title = serializers.CharField(source='book.title', read_only=True)
    book_author = serializers.CharField(source='book.author', read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Borrow
        fields = '__all__'
        read_only_fields = ['user', 'borrowed_at', 'returned_at']

    def validate(self, data):
        book = data.get('book')
        user = self.context['request'].user
        
        if not book.available:
            raise serializers.ValidationError("Book is not available")
        
        if Borrow.objects.filter(user=user, book=book, returned=False).exists():
            raise serializers.ValidationError("You have already borrowed this book")
        
        return data