# permissions.py
from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied

class IsBusinessUserOwner(permissions.BasePermission):
    """
    Erlaubt Zugriff nur dem Business-User selbst.
    """
    def has_permission(self, request, view):
        # Prüfe, ob der Benutzer authentifiziert ist
        if not request.user.is_authenticated:
            return False
        
        # Prüfe, ob der Benutzer ein Business-Profil hat
        if not hasattr(request.user, 'profile') or request.user.profile.type != 'business':
            raise PermissionDenied("Nur Business-Nutzer dürfen diese Aktion ausführen.")
        
        # Prüfe, ob die angefragete business_user_id mit der User-ID übereinstimmt
        requested_user_id = view.kwargs.get('business_user_id')
        return str(request.user.id) == str(requested_user_id)