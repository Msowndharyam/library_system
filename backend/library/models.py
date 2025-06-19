from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.exceptions import ValidationError

class User(AbstractUser):
    ROLE_CHOICES = (
        ('user', 'User'),
        ('librarian', 'Librarian'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user')
    email = models.EmailField(unique=True)

    def __str__(self):
        return f"{self.username} ({self.role})"

class Book(models.Model):
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    genre = models.CharField(max_length=100)
    available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['title', 'author'],
                name='unique_book_title_author'
            )
        ]

    def clean(self):
        if not self.title.strip():
            raise ValidationError({'title': 'Title cannot be empty'})
        if not self.author.strip():
            raise ValidationError({'author': 'Author cannot be empty'})
        if not self.genre.strip():
            raise ValidationError({'genre': 'Genre cannot be empty'})

    def __str__(self):
        return f"{self.title} by {self.author}"

class Borrow(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='borrows')
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='borrows')
    borrowed_at = models.DateTimeField(auto_now_add=True)
    due_date = models.DateField()
    returned = models.BooleanField(default=False)
    returned_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ['user', 'book', 'returned']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'book'],
                condition=models.Q(returned=False),
                name='unique_active_borrow'
            )
        ]

    def clean(self):
        if self.returned and not self.returned_at:
            from django.utils import timezone
            self.returned_at = timezone.now()

    def __str__(self):
        status = "Returned" if self.returned else "Active"
        return f"{self.user.username} - {self.book.title} ({status})"
