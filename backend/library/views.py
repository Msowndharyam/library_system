from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.pagination import PageNumberPagination
from rest_framework.exceptions import ValidationError, PermissionDenied
from django.utils import timezone
from django.db.models import Q
from .models import User, Book, Borrow
from .serializers import RegisterSerializer, BookSerializer, BorrowSerializer
from .permissions import IsLibrarian, IsLibrarianOrReadOnly

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class RegisterViewSet(viewsets.GenericViewSet):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {"message": "User registered successfully", "user_id": user.id},
            status=status.HTTP_201_CREATED
        )

class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all().order_by('-created_at')
    serializer_class = BookSerializer
    permission_classes = [IsLibrarianOrReadOnly]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['title', 'author', 'genre']
    ordering_fields = ['title', 'author', 'created_at']
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = Book.objects.all()
        available_only = self.request.query_params.get('available', None)
        if available_only is not None:
            queryset = queryset.filter(available=True)
        return queryset.order_by('-created_at')

    @action(detail=False, methods=['get'])
    def available(self, request):
        available_books = Book.objects.filter(available=True)
        page = self.paginate_queryset(available_books)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(available_books, many=True)
        return Response(serializer.data)

class BorrowViewSet(viewsets.ModelViewSet):
    serializer_class = BorrowSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'role') and user.role == 'librarian':
            return Borrow.objects.all().order_by('-borrowed_at')
        else:
            return Borrow.objects.filter(user=user).order_by('-borrowed_at')

    def perform_create(self, serializer):
        book = serializer.validated_data['book']
        
        if not book.available:
            raise ValidationError("Book is not available")
        
        borrow = serializer.save(user=self.request.user)
        
        book.available = False
        book.save()

    def perform_update(self, serializer):
        instance = serializer.save()
        
        if instance.returned and not instance.returned_at:
            instance.returned_at = timezone.now()
            instance.save()
            
            instance.book.available = True
            instance.book.save()

    @action(detail=False, methods=['get'])
    def my_borrows(self, request):
        borrows = Borrow.objects.filter(user=request.user).order_by('-borrowed_at')
        page = self.paginate_queryset(borrows)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(borrows, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def overdue(self, request):
        if not (hasattr(request.user, 'role') and request.user.role == 'librarian'):
            raise PermissionDenied("Only librarians can view overdue books")
        
        today = timezone.now().date()
        overdue_borrows = Borrow.objects.filter(
            due_date__lt=today,
            returned=False
        ).order_by('due_date')
        
        page = self.paginate_queryset(overdue_borrows)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(overdue_borrows, many=True)
        return Response(serializer.data)
