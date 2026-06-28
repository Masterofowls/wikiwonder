"""Wiki page edit permissions."""
from apps.wiki.models import WikiPage


def can_edit_page(user, page: WikiPage) -> bool:
    if not user.is_authenticated:
        return False
    if user.is_staff:
        return True
    return page.author_id == user.id
