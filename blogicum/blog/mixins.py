from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect


class AuthorOnlyMixin(LoginRequiredMixin):
    """Пускает к изменению объекта только его автора."""

    def get_author_object(self, kwargs):
        raise NotImplementedError

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        obj = self.get_author_object(kwargs)
        if obj.author_id != request.user.id:
            post_id = getattr(obj, 'post_id', obj.pk)
            return redirect('blog:post_detail', post_id=post_id)
        return super().dispatch(request, *args, **kwargs)


class PostAuthorMixin(AuthorOnlyMixin):
    def get_author_object(self, kwargs):
        from .models import Post
        return get_object_or_404(Post, pk=kwargs['post_id'])


class CommentAuthorMixin(AuthorOnlyMixin):
    """Пускает к комментарию только его автора."""

    def get_author_object(self, kwargs):
        from .models import Comment
        return get_object_or_404(
            Comment,
            pk=kwargs['comment_id'],
            post_id=kwargs['post_id'],
        )
