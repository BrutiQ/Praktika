from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from .forms import PostForm, CommentForm
from .models import Group, Post, User, Follow

from yatube.settings import POSTS_PER_PAGE


def pagination(request, objects):
    return Paginator(objects, POSTS_PER_PAGE).get_page(
        request.GET.get('page'))


def index(request):
    return render(request, 'posts/index.html', {
        'page_obj': pagination(request, Post.objects.all()),
    })


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    return render(request, 'posts/group_list.html', {
        'group': group,
        'page_obj': pagination(request, group.posts.all()),
    })


def profile(request, username):
    author = get_object_or_404(User, username=username)
    return render(request, 'posts/profile.html', {
        'page_obj': pagination(request, author.posts.all()),
        'author': author,
        'following': (request.user.is_authenticated
                      and request.user.username != username
                      and Follow.objects.filter(
                          user=request.user,
                          author=author).exists()),
    })


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    return render(request, 'posts/post_detail.html', {
        'post': post,
        'form': CommentForm(),
    })


@login_required
def add_comment(request, post_id):
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = get_object_or_404(Post, pk=post_id)
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def post_create(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if not form.is_valid():
        return render(request, 'posts/create_post.html', {
            'form': form, 'is_edit': False})
    post = form.save(commit=False)
    post.author = request.user
    post.save()
    return redirect('posts:profile', username=post.author)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post_id=post_id)
    form = PostForm(
        request.POST or None, files=request.FILES or None, instance=post)
    if not form.is_valid():
        return render(request, 'posts/create_post.html', {
            'form': form, 'is_edit': True})
    post = form.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    return render(request, 'posts/follow.html', {
        'page_obj': pagination(request, Post.objects.filter(
            author__following__user=request.user)),
    })


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if author == request.user:
        return redirect('posts:profile', username=username)
    follower = Follow.objects.filter(
        user=request.user,
        author=author
    ).exists()
    if follower is True:
        return redirect('posts:profile', username=username)
    Follow.objects.create(user=request.user, author=author)
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    get_object_or_404(Follow.objects.filter(
        author__username=username, user=request.user)).delete()
    return redirect('posts:profile', username=username)