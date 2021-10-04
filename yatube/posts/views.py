from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User
from .utils import posts_page


@cache_page(20)
def index(request):
    return render(request, 'posts/index.html', {
        'page_obj': posts_page(request, Post.objects.all()),
    })


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    return render(request, 'posts/group_list.html', {
        'group': group,
        'page_obj': posts_page(request, group.posts.all()),
    })


def profile(request, username):
    author = get_object_or_404(User, username=username)
    following = (
        (request.user.is_authenticated)
        and (author != request.user)
        and (request.user.follower.count() != 0)
        and (Follow.objects.filter(
            author=author,
            user=request.user
        ).exists())
    )
    return render(request, 'posts/profile.html', {
        'following': following,
        'author': author,
        'page_obj': posts_page(request, author.posts.all()),
    })


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    return render(request, 'posts/post_detail.html', {
        'post': post,
        'form': form,
        'comments': post.comments.all()
    })


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post_id=post.id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id=post.id)
    return render(request, 'posts/create_post.html', {
        'form': form,
        'is_edit': True
    })


@login_required
def post_create(request):
    form = PostForm(
        request.POST or None,
        files=request.FILES or None
    )
    if not form.is_valid():
        return render(request, 'posts/create_post.html', {
            'form': form
        })
    post = form.save(commit=False)
    post.author = request.user
    form.save()
    return redirect('posts:profile', username=request.user.username)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    page_obj = posts_page(
        request,
        Post.objects.filter(author__following__user=request.user)
    )
    return render(request, 'posts/follow.html', {
        'page_obj': page_obj
    })


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if author != request.user:
        Follow.objects.get_or_create(
            author=author,
            user=request.user
        )
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    if (
        request.user.is_authenticated
        and request.user.follower.count() != 0
    ):
        get_object_or_404(
            Follow,
            author=author,
            user=request.user
        ).delete()
    return redirect('posts:profile', username=username)
