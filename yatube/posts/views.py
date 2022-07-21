from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page
from django.shortcuts import redirect
from django.urls import reverse


from .models import Group, Post, User, Follow
from .forms import PostForm, CommentForm
from .utils import paginator_project


@cache_page(20, key_prefix='index_page')
def index(request):
    post_list = Post.objects.select_related('author').all()
    page_obj = paginator_project(request, post_list)
    context = {'page_obj': page_obj}
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    page_obj = paginator_project(request, posts)
    context = {'group': group, 'posts': posts, 'page_obj': page_obj}
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts = Post.objects.filter(author_id=author)
    page_obj = paginator_project(request, posts)
    following = request.user.is_authenticated and Follow.objects.filter(
        user=request.user, author=author
    ).exists()
    profile = author
    context = {
        'page_obj': page_obj,
        'author': author,
        'following': following,
        'profile': profile
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    comments = post.comments.all()
    context = {
        'post': post,
        'comments': comments,
        'form': CommentForm(),
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    if request.method == 'POST':
        form = PostForm(
            request.POST or None,
            files=request.FILES or None
        )
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('posts:profile', request.user.username)
        else:
            return render(request, 'posts/create_post.html',
                          {'form': form, })
    else:
        form = PostForm()
        return render(request, 'posts/create_post.html',
                      {'form': form, })


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = PostForm(instance=post)
    if request.user != post.author:
        return redirect("posts:profile", post_id=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post)
    if form.is_valid():
        form.save()
        return redirect("posts:post_detail", post_id)
    else:
        return render(request, 'posts/create_post.html',
                               {'form': form,
                                'is_edit': True,
                                'post': post, }
                      )


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
    follow_list = Post.objects.filter(author__following__user=request.user)
    page_obj = paginator_project(request, follow_list)
    context = {'page_obj': page_obj}
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    user = request.user
    author = User.objects.get(username=username)
    is_follower = Follow.objects.filter(user=user, author=author)
    if user != author and not is_follower.exists():
        Follow.objects.create(user=user, author=author)
    return redirect(reverse('posts:profile', args=[username]))


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    is_follower = Follow.objects.filter(user=request.user, author=author)
    if is_follower.exists():
        is_follower.delete()
    return redirect('posts:profile', username=author)
