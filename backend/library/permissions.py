from rest_framework import permissions

class IsLibrarian(permissions.BasePermission):
    """
    Custom permission to only allow librarians to perform certain actions.
    """
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            hasattr(request.user, 'role') and 
            request.user.role == 'librarian'
        )

class IsLibrarianOrReadOnly(permissions.BasePermission):
    """
    Custom permission to allow read-only access to all authenticated users,
    but write access only to librarians.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        return (
            request.user and 
            request.user.is_authenticated and 
            hasattr(request.user, 'role') and 
            request.user.role == 'librarian'
        )