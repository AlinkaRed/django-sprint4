from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse


class AuthorOnlyMixin(LoginRequiredMixin):
    """Пускает к изменению объекта только его автора."""

    def get_author_object(self, kwargs):
        raise NotImplementedError

    def get_author_redirect_url(self, obj):
        raise NotImplementedError

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        obj = self.get_author_object(kwargs)
        if obj.author != request.user:
            return redirect(self.get_author_redirect_url(obj))
        return super().dispatch(request, *args, **kwargs)


class PostAuthorMixin(AuthorOnlyMixin):
    def get_author_object(self, kwargs):
        from .models import Post
        return get_object_or_404(Post, pk=kwargs['post_id'])

    def get_author_redirect_url(self, obj):
        return reverse('blog:post_detail', kwargs={'post_id': obj.pk})


class CommentAuthorMixin(AuthorOnlyMixin):
    """Пускает к комментарию только его автора."""

    def get_author_object(self, kwargs):
        from .models import Comment
        return get_object_or_404(
            Comment,
            pk=kwargs['comment_id'],
            post_id=kwargs['post_id'],
        )

    def get_author_redirect_url(self, obj):
        return reverse(
            'blog:post_detail',
            kwargs={'post_id': obj.post_id},
        )
