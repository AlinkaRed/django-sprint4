from django.contrib.auth import get_user_model, login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from .constants import POSTS_PER_PAGE
from .forms import CommentForm, PostForm, UserEditForm
from .mixins import CommentAuthorMixin, PostAuthorMixin
from .models import Category, Comment, Post

User = get_user_model()


def post_is_public(post):
    """Публикация видна всем: опубликована, категория жива, дата наступила."""
    return (
        post.is_published
        and post.pub_date <= timezone.now()
        and post.category_id is not None
        and post.category.is_published
    )


class PostListView(ListView):
    model = Post
    template_name = 'blog/index.html'
    paginate_by = POSTS_PER_PAGE

    def get_queryset(self):
        return Post.objects.published().with_related()


class PostDetailView(DetailView):
    model = Post
    template_name = 'blog/detail.html'
    pk_url_kwarg = 'post_id'
    context_object_name = 'post'

    def get_object(self, queryset=None):
        post = get_object_or_404(
            Post.objects.select_related(
                'author',
                'category',
                'location',
            ),
            pk=self.kwargs['post_id'],
        )
        is_author = (
            self.request.user.is_authenticated
            and post.author_id == self.request.user.id
        )
        if is_author or post_is_public(post):
            return post
        raise Http404

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CommentForm()
        context['comments'] = self.object.comments.select_related(
            'author',
        ).order_by('created_at')
        return context


class CategoryPostsView(ListView):
    model = Post
    template_name = 'blog/category.html'
    paginate_by = POSTS_PER_PAGE

    def get_queryset(self):
        self.category = get_object_or_404(
            Category,
            slug=self.kwargs['category_slug'],
            is_published=True,
        )
        return (
            Post.objects.filter(category=self.category)
            .published()
            .with_related()
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        return context


class ProfileView(ListView):
    model = Post
    template_name = 'blog/profile.html'
    paginate_by = POSTS_PER_PAGE

    def get_queryset(self):
        self.profile = get_object_or_404(
            User,
            username=self.kwargs['username'],
        )
        posts = Post.objects.filter(author=self.profile).with_related()
        if self.request.user != self.profile:
            posts = posts.published()
        return posts

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = self.profile
        return context


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = UserEditForm
    template_name = 'blog/user.html'

    def get_object(self, queryset=None):
        return self.request.user

    def get_success_url(self):
        return reverse(
            'blog:profile',
            kwargs={'username': self.object.username},
        )


class RegistrationView(CreateView):
    form_class = UserCreationForm
    template_name = 'registration/registration_form.html'
    success_url = reverse_lazy('blog:index')

    def form_valid(self, form):
        response = super().form_valid(form)
        login(
            self.request,
            self.object,
            backend='django.contrib.auth.backends.ModelBackend',
        )
        return response


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            'blog:profile',
            kwargs={'username': self.request.user.username},
        )


class PostUpdateView(PostAuthorMixin, UpdateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'

    def get_success_url(self):
        return reverse(
            'blog:post_detail',
            kwargs={'post_id': self.object.pk},
        )


class PostDeleteView(PostAuthorMixin, DeleteView):
    model = Post
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'
    success_url = reverse_lazy('blog:index')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = PostForm(instance=self.object)
        return context


class CommentCreateView(LoginRequiredMixin, CreateView):
    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.post = get_object_or_404(
            Post,
            pk=self.kwargs['post_id'],
        )
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            'blog:post_detail',
            kwargs={'post_id': self.kwargs['post_id']},
        )


class CommentUpdateView(CommentAuthorMixin, UpdateView):
    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_id'
    context_object_name = 'comment'

    def get_object(self, queryset=None):
        return get_object_or_404(
            Comment,
            pk=self.kwargs['comment_id'],
            post_id=self.kwargs['post_id'],
        )

    def get_success_url(self):
        return reverse(
            'blog:post_detail',
            kwargs={'post_id': self.kwargs['post_id']},
        )


class CommentDeleteView(CommentAuthorMixin, DeleteView):
    model = Comment
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_id'
    context_object_name = 'comment'

    def get_object(self, queryset=None):
        return get_object_or_404(
            Comment,
            pk=self.kwargs['comment_id'],
            post_id=self.kwargs['post_id'],
        )

    def get_success_url(self):
        return reverse(
            'blog:post_detail',
            kwargs={'post_id': self.kwargs['post_id']},
        )
