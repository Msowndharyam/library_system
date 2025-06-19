from django.contrib import admin
from .models import User, Book, Borrow

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'email', 'role', 'is_staff')
    list_filter = ('role',)
    search_fields = ('username', 'email')
    ordering = ('id',)

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'author', 'genre', 'available')
    list_filter = ('genre', 'available')
    search_fields = ('title', 'author')
    ordering = ('id',)

@admin.register(Borrow)
class BorrowAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'book', 'borrowed_at', 'due_date', 'returned')
    list_filter = ('returned', 'due_date')
    search_fields = ('user__username', 'book__title')
    ordering = ('-borrowed_at',)
