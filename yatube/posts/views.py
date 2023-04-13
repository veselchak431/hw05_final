from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page


from .forms import PostForm, CommentForm
from .models import Group, Post, User, Comment, Follow

POSTS_ON_PAGE = 10
TITLE_POST_LENGTH = 30


def get_paginator_context(queryset, request):
    paginator = Paginator(queryset, POSTS_ON_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return {
        'page_number': page_number,
        'page_obj': page_obj,
    }


@cache_page(20 * 60)
def index(request):
    template = 'posts/index.html'
    posts = Post.objects.all()
    title = 'Последние обновления на сайте'
    context = {'title': title}
    context.update(get_paginator_context(posts, request))
    return render(request, template, context)


def group_posts(request, slug):
    template = 'posts/group_list.html'
    group = get_object_or_404(Group, slug=slug)
    posts = group.post_set.all()
    title = f'группа {group.title}'
    context = {'group': group,
               'title': title}
    context.update(get_paginator_context(posts, request))
    return render(request, template, context)


def profile(request, username):
    template = 'posts/profile.html'
    author = get_object_or_404(User, username=username)
    posts = Post.objects.filter(author=author)

    if request.user.is_authenticated:
        following = Follow.objects.filter(
            user=request.user, author=author).exists()
    else:
        following = False
    posts_count = posts.count()
    title = f'Профайл пользователя {author}'
    context = {
        'title': title,
        'author': author,
        'posts_count': posts_count,
        'following': following
    }
    context.update(get_paginator_context(posts, request))
    return render(request, template, context)


def post_detail(request, post_id):
    template = 'posts/post_detail.html'

    post = get_object_or_404(Post, id=post_id)
    posts_fragment = post.text[:TITLE_POST_LENGTH]
    title = f'Пост {posts_fragment}'
    if request.user == post.author:
        is_edit = True
    else:
        is_edit = False
    posts_count = Post.objects.filter(author=post.author).count()
    comments = Comment.objects.all()
    form = CommentForm()
    context = {
        'title': title,
        'post': post,
        'posts_count': posts_count,
        'is_edit': is_edit,
        'comments': comments,
        'form': form

    }
    return render(request, template, context)


@login_required(redirect_field_name='login')
def post_create(request):
    if request.method == 'POST':
        form = PostForm(request.POST or None, files=request.FILES or None)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('posts:profile', post.author)
    else:
        form = PostForm()
    return render(request, 'posts/create_post.html', {'form': form})


def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if not request.user == post.author:
        return redirect('posts:post_detail', post_id)

    if request.method == 'POST':
        form = PostForm(request.POST or None, files=request.FILES or None)
        if form.is_valid():
            post.text = form.cleaned_data['text']
            post.group = form.cleaned_data['group']
            post.save()
            return redirect('posts:post_detail', post_id)
    else:
        form = PostForm(instance=post)
    return render(request, 'posts/create_post.html',
                  {'form': form, 'is_edit': True})


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
    if not request.user.is_authenticated:
        redirect('posts:index')
    authors = Follow.objects.filter(user=request.user).values('author')
    posts = Post.objects.filter(author__in=authors)
    title = 'Подписки'
    context = {'title': title}
    context.update(get_paginator_context(posts, request))
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if author != request.user:
        Follow.objects.get_or_create(user=request.user,
                                     author=author)
    return redirect('posts:profile', username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(user=request.user,
                          author=author).delete()
    return redirect('posts:profile', username)
