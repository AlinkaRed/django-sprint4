from django.core.paginator import Paginator
from django.db.models import Count
from django.utils import timezone

from .constants import POSTS_PER_PAGE


def get_posts_with_comments(queryset):
    """Аннотация числом комментариев и сортировка от новых к старым."""
    return (
        queryset.select_related(
            'author',
            'category',
            'location',
        )
        .annotate(comment_count=Count('comments'))
        .order_by('-pub_date', '-id')
    )


def filter_published(queryset):
    """Оставляет только опубликованные посты с опубликованной категорией."""
    return queryset.filter(
        is_published=True,
        category__is_published=True,
        pub_date__lte=timezone.now(),
    )


def get_paginated_page(request, queryset):
    """Возвращает одну страницу пагинатора."""
    paginator = Paginator(queryset, POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)
